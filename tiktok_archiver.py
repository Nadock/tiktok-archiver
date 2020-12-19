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
    parser.add_argument("output")
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
    # print(f"{args=}")
    archive_path = extract_archvie(args.archive_path)
    # print(f"{archive_path=}")
    archive_videos = discover_videos(archive_path)

    if "favourites" in args.save:
        # print(f"Found {len(archive_videos.favourites)} videos in your favourites")
        if archive_videos.favourites:
            # print(f"For example: {archive_videos.favourites[0]}")
            download_videos(archive_videos.favourites, args.output)

    if "likes" in args.save:
        # print(f"Found {len(archive_videos.likes)} videos in your likes")
        if archive_videos.likes:
            # print(f"For example: {archive_videos.likes[0]}")
            download_videos(archive_videos.likes, args.output)

    if "uploads" in args.save:
        # print(f"Found {len(archive_videos.uploads)} videos in your uploads")
        if archive_videos.uploads:
            # print(f"For example: {archive_videos.uploads[0]}")
            download_videos(archive_videos.uploads, args.output)

    if "history" in args.save:
        # print(f"Found {len(archive_videos.history)} videos in your browsing history")
        if archive_videos.history:
            # print(f"For example: {archive_videos.history[0]}")
            download_videos(archive_videos.history, args.output)


def extract_archvie(archive_path: str) -> pathlib.Path:
    path = pathlib.Path(archive_path)

    if path.is_dir():
        return path

    if path.is_file():
        temp_dir = tempfile.mkdtemp()

        with zipfile.ZipFile(path) as zfile:
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
            # Date: 2020-08-12 02:16:22
            # Video Link: https://www.tiktokv.com/share/video/6850067280781446406/
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

    for video in videos:
        print(f"Dowloading {video.link} ...", end="\r", file=sys.stderr)

        try:
            subprocess.run(
                yt_dl_args + [video.link], capture_output=True, check=True, text=True
            )
        except subprocess.CalledProcessError as ex:
            error = str(ex.stderr).split("\n")[0]
            print(f"Dowloading {video.link} FAILED ❌:\n\t{error}", file=sys.stderr)

        print(f"Dowloading {video.link} DONE ✅", file=sys.stderr)


if __name__ == "__main__":
    main()
