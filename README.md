# automudo
Autonomous Music Downloader

## What does it do?
automudo downloads the music that you have in your bookmarks for you.  
It aims to be as autonomous as possible and minimize your downloading efforts.

## How does it work?
- it looks for a folder named "music" in your browser's bookmarks
- it looks for a matching album for each bookmark under this folder
- it downloads the albums from your favorite torrents tracker

## Running automudo
- Download and install Python 3 (automudo does not support Python 2)
- Download automudo
- Copy config-sample.yaml to config.yaml and edit config.yaml
- Run automudo using `python3 -m scripts.automudo`
- If you wish, you can install automudo using the provided setup.py