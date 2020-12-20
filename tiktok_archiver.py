#!/usr/bin/env python3
import argparse
import dataclasses
import datetime
import pathlib
import subprocess
import sys
import tempfile
import zipfile
from functools import partial
from multiprocessing import dummy
from typing import List


@dataclasses.dataclass
class Video:
    """
    A TikTok video as represented in a user data export.

    `link` is a URL to the TikTok video.
    `datetime` is the date associated with the video in the user data export.
    """

    link: str
    datetime: str

    def __post_init__(self):
        self._clean_link()
        self._clean_datetime()

    def _clean_link(self):
        self.link = self.link.replace(" ", "").replace("\n", "")

    def _clean_datetime(self):
        self.datetime = datetime.datetime.strptime(
            self.datetime.replace("\n", "").strip(),
            "%Y-%m-%d %H:%M:%S",
        ).isoformat()


@dataclasses.dataclass
class ArchiveVideos:
    """
    The TikTok video collections as represented in a user data export.

    `favourites` is the list of TikTok videos the user has favourited.
    `likes` is the list of TikTok videos the user has liked.
    `uploads` is the list of TikTok videos the user has uploaded.
    `history` is the list of TikTok videos the user has viewed.
    """

    favourites: List[Video]
    likes: List[Video]
    uploads: List[Video]
    history: List[Video]


def _init_argparse():
    """Prepare an `argparse.ArgumentParser` and use it to parse the CLI command."""
    parser = argparse.ArgumentParser()

    parser.add_argument("archive_path")
    parser.add_argument("output_path")
    parser.add_argument(
        "--save",
        default=[],
        choices=["favourites", "likes", "uploads", "history"],
        action="append",
    )
    parser.add_argument("--parallel", default=20, type=int)

    args = parser.parse_args()
    return args


def extract_archvie(archive_path: pathlib.Path) -> pathlib.Path:
    """
    Extract a user data archive to a temporary directory.

    If the user supplied a path to an already unzipped archive, this is a no-op and will
    return the same path. Otherwise, the archive is unzipped to a system temporary
    directory and that path is returned.
    """
    if archive_path.is_dir():
        return archive_path

    if archive_path.is_file():
        temp_dir = tempfile.mkdtemp()

        with zipfile.ZipFile(archive_path) as zfile:
            zfile.extractall(temp_dir)

        return pathlib.Path(temp_dir)

    raise ValueError(f"{archive_path} is not a directory or zip file")


def discover_videos(archive_path: pathlib.Path) -> ArchiveVideos:
    """
    Read the video history files in a user data export to discover the favourites,
    likes, uploads, and history lists.
    """
    return ArchiveVideos(
        favourites=read_videos(archive_path / "Activity" / "Favorite Videos.txt"),
        likes=read_videos(archive_path / "Activity" / "Like List.txt"),
        uploads=read_videos(archive_path / "Videos" / "Videos.txt"),
        history=read_videos(archive_path / "Activity" / "Video Browsing History.txt"),
    )


def read_videos(file_path: pathlib.Path) -> List[Video]:
    """Read a video history file and return a list of all the listed videos."""
    videos: List[Video] = []
    date_time = None
    link = None

    if not file_path.is_file():
        return videos

    with open(file_path) as path:
        # TODO: Maybe use a state machine to parse the video files more reliably
        for line in path.readlines():
            if line.startswith("Date: "):
                date_time = line.split(":", 1)[1]
            elif line.startswith("Video Link:"):
                link = line.split(":", 1)[1]

            if date_time and link:
                videos.append(Video(datetime=date_time, link=link))
                date_time = None
                link = None

    return videos


def download_videos(videos: List[Video], output: pathlib.Path, threads: int = 20):
    """
    Download a list of TikTok videos into an output directory.

    `threads` controlls the number of parrallel instances of youtube-dl used to download
    TikTok videos. More threads better saturate available network and disk bandwidth but
    increases the likley hood that TikTok throttles or temporarily bans our connections.
    """
    print(f"Downloading {len(videos)} videos to {output.absolute()}", file=sys.stderr)

    # Build a list of each individual youtube-dl command to run
    commands = [
        [
            "youtube-dl",
            "--write-info-json",
            "--ignore-errors",
            "--output",
            f"{output}/%(id)s.%(ext)s",
            video.link,
        ]
        for video in videos
    ]

    # Run each of the youtube-dl tasks in a thread pool
    results: List[subprocess.CompletedProcess] = dummy.Pool(threads).imap(
        partial(subprocess.run, capture_output=True, text=True), commands
    )

    # Wait for each subprocess to complete and display details of the result
    done_count = 0
    for result in results:
        done_count += 1
        if result.returncode == 0:
            print(
                f"Dowloading ({done_count}/{len(videos)}) {result.args[-1]}\tDONE ✅",
                file=sys.stderr,
            )
        else:
            error = result.stderr.split("\n", 1)[0]
            print(
                (
                    f"Dowloading ({done_count}/{len(videos)}) {result.args[-1]}\t"
                    f"FAILED ❌: \n\t{error}"
                ),
                file=sys.stderr,
            )


def main():
    """Parse command line args and download the requested videos."""
    args = _init_argparse()

    archive_path = pathlib.Path(args.archive_path)
    output_path = pathlib.Path(args.output_path)

    archive_path = extract_archvie(archive_path)
    archive_videos = discover_videos(archive_path)

    if "favourites" in args.save:
        if archive_videos.favourites:
            download_videos(
                archive_videos.favourites, output_path / "favourites", args.parallel
            )

    if "likes" in args.save:
        if archive_videos.likes:
            download_videos(archive_videos.likes, output_path / "likes", args.parallel)

    if "uploads" in args.save:
        if archive_videos.uploads:
            download_videos(
                archive_videos.uploads, output_path / "uploads", args.parallel
            )

    if "history" in args.save:
        if archive_videos.history:
            download_videos(
                archive_videos.history, output_path / "history", args.parallel
            )


if __name__ == "__main__":
    main()
