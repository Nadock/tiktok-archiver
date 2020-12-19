# TikTok Archiver

Archive copies of your favourite TikTok videos.

## WIP NOTICE

Above the stanard "use at your own risk" disclaimers, fair warning this is very much a
prototype solution and could do all sorts of dumb things. If you observe it doing
something dumb please open an [Issue](https://github.com/Nadock/tiktok-archiver/issues).

## Installing

Currently the only way to get the script is to clone the repository:

```bash
$> git clone git@github.com:Nadock/tiktok-archiver.git
$> cd ./tiktok-archiver
```

Then you should use [`pipenv`](https://github.com/pypa/pipenv) to setup a virtual
environment that contains everything needed to run the script:

```bash
$> pipenv install
$> pipenv shell
```

## Getting a copy of your TikTok data

The instructions are correct as of writing, however there maybe differences between app
version and OS types. These instructions worked on an iPhone 12, running iOS 14.1, with
TikTok version 18.2.0.

1. Open the TikTok app on your device
1. Select **Me** at the bottom of the screen
1. Select the **...** at the top of the **Me** screen
1. Open the **Privacy** menu
1. Open the **Personalization and data** menu
1. Open the **Download your data** menu
1. Select **Request data file**
1. Wait the day or two required for TikTok to process your request
1. Download the archive from TikTok and transfer it to your computer

## Running the script

One of the first features I want to improve is the script's `--help` output, but for now
it's a bit lacklustre. To save all the currently supported video types, try this
example:

```bash
$> ./tiktok_archiver.py --save favourites --save likes --save uploads --save history {archive_path} {output_path}
```
