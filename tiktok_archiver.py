#!/usr/bin/env python3
import argparse
import tempfile
import zipfile
import pathlib
import dataclasses
import datetime
import subprocess
import sys
from typing import List


@dataclasses.dataclass
class Video:
    link: str
    datetime: str

    def __post_init__(self):
        self.link = self.normalise_link()
        self.datetime = self.normalise_datetime()

    def normalise_link(self):
        return self.link.replace(" ", "").replace("\n", "")

    def normalise_datetime(self) -> str:
        clean_dt = self.datetime.replace("\n", "").strip()
        dt = datetime.datetime.strptime(clean_dt, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()


@dataclasses.dataclass
class ArchiveVideos:
    favourites: List[Video]
    likes: List[Video]
    uploads: List[Video]
    history: List[Video]


def _init_argparse():
    parser = argparse.ArgumentParser()

    parser.add_argument("archive_path")
    parser.add_argument("output_path")
    parser.add_argument(
        "--save",
        default=[],
        choices=["favourites", "likes", "uploads", "history"],
        action="append",
    )

    args = parser.parse_args()
    return args


def main():
    args = _init_argparse()

    archive_path = pathlib.Path(args.archive_path)
    output_path = pathlib.Path(args.output_path)

    archive_path = extract_archvie(archive_path)
    archive_videos = discover_videos(archive_path)

    if "favourites" in args.save:
        if archive_videos.favourites:
            download_videos(archive_videos.favourites, output_path / "favourites")

    if "likes" in args.save:
        if archive_videos.likes:
            download_videos(archive_videos.likes, output_path / "likes")

    if "uploads" in args.save:
        if archive_videos.uploads:
            download_videos(archive_videos.uploads, output_path / "uploads")

    if "history" in args.save:
        if archive_videos.history:
            download_videos(archive_videos.history, output_path / "history")


def extract_archvie(archive_path: pathlib.Path) -> pathlib.Path:
    if archive_path.is_dir():
        return archive_path

    if archive_path.is_file():
        temp_dir = tempfile.mkdtemp()

        with zipfile.ZipFile(archive_path) as zfile:
            zfile.extractall(temp_dir)

        return pathlib.Path(temp_dir)

    raise ValueError(f"{archive_path} is not a directory or zip file")


def discover_videos(archive_path: pathlib.Path):

    favourites = read_videos(archive_path / "Activity" / "Favorite Videos.txt")
    likes = read_videos(archive_path / "Activity" / "Like List.txt")
    uploads = read_videos(archive_path / "Videos" / "Videos.txt")
    history = read_videos(archive_path / "Activity" / "Video Browsing History.txt")

    return ArchiveVideos(
        favourites=favourites,
        likes=likes,
        uploads=uploads,
        history=history,
    )


def read_videos(file_path: pathlib.Path):
    datetime = None
    link = None

    videos = []

    if not file_path.is_file():
        return []

    with open(file_path) as path:
        for line in path.readlines():
            if line.startswith("Date: "):
                datetime = line.split(":", 1)[1]
            elif line.startswith("Video Link:"):
                link = line.split(":", 1)[1]

            if datetime and link:
                videos.append(Video(datetime=datetime, link=link))
                datetime = None
                link = None

    return videos


def download_videos(videos: List[Video], output: pathlib.Path):
    yt_dl_args = [
        "youtube-dl",
        "--write-info-json",
        "--ignore-errors",
        "--output",
        f"{output}/%(id)s.%(ext)s",
    ]

    print(f"Downloading {len(videos)} videos to {output}")

    for idx, video in enumerate(videos):
        print(
            f"Dowloading ({idx+1}/{len(videos)}) {video.link} ...",
            end="\r",
            file=sys.stderr,
        )

        try:
            subprocess.run(
                yt_dl_args + [video.link], capture_output=True, check=True, text=True
            )
        except subprocess.CalledProcessError as ex:
            error = str(ex.stderr).split("\n")[0]
            print(
                f"Dowloading ({idx+1}/{len(videos)}) {video.link} FAILED ❌:\n\t{error}",
                file=sys.stderr,
            )

        print(
            f"Dowloading ({idx+1}/{len(videos)}) {video.link} DONE ✅", file=sys.stderr
        )


if __name__ == "__main__":
    main()
