# automudo
Autonomous Music Downloader

## What does it do?
automudo downloads the music you have in your bookmarks for you.
It aims to require as minimum user interaction as possible
and do anything as autonomously as possible.

## How does it work?
- it looks for a folder named "music" in your browser's bookmarks
- it looks for a matching album for each bookmark under this folder
- it downloads the albums from your favorite torrents tracker

## Running automudo
- Download and install Python 3 (automudo does not support Python 2)
- Download automudo
- Copy config.py.sample to config.py and edit it (REQUIRED, don't skip this)
- Run automudo using `python3 -m scripts.automudo`
- If you wish, you can install automudo using the provided setup.py