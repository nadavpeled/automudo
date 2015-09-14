import os
import re
import sys

from automudo.ui import cui
from automudo.trackers.rutracker import Rutracker
from automudo.music_bookmarks import get_user_music_bookmarks
from automudo.albums_to_download import find_albums_to_download
from automudo import config


def find_torrents_of_albums(albums_titles, tracker):
    """
    Finds torrents of the given albums in the given tracker.
    Returns a list of tuples in the form (torrent-id, album-title).

    Note: interacts with the user for selecting
          a matching torrent for each album
    """
    for album_title in albums_titles:
        print("Looking for torrents matching '{}'..".format(
            cui.get_printable_string(" - ".join(album_title))
            ))
        available_torrents = tracker.find_torrents_by_title(album_title)

        def print_torrent_description(result_number, result):
            _, torrent_title = result
            print("{}. {}".format(
                result_number,
                cui.get_printable_string(torrent_title)
                ))
            print()

        try:
            chosen_item = cui.let_user_choose_item(
                                  available_torrents,
                                  config.ITEMS_PER_PAGE,
                                  print_torrent_description,
                                  "Please choose a torrent",
                                  config.TORRENT_AUTOSELECTION_MODE
                                  )
        except cui.NoMoreItemsError:
            print("No matching torrents found.")
            print()
            continue

        if chosen_item:
            torrent_id, _ = chosen_item
            yield (torrent_id, album_title)


def download_albums_torrents(albums_titles, tracker, torrents_dir):
    """
    Downloads torrents for music albums.

    Parameters:
        albums_titles - the titles of the albums to download
        tracker - the tracker to download from
        torrents_dir - the directory into which the torrents will be saved
    """
    torrents = find_torrents_of_albums(albums_titles, tracker)
    for (torrent_id, album_title) in torrents:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            " - ".join(album_title) + ' [{}].torrent'.format(torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)
        with open(torrent_file_path, "wb") as f:
            f.write(tracker.get_torrent_file_contents(torrent_id))


def main():
    user_music_bookmarks = get_user_music_bookmarks()
    albums_titles = find_albums_to_download(user_music_bookmarks)

    tracker = Rutracker(config.RUTRACKER_USERNAME,
                        config.RUTRACKER_PASSWORD,
                        config.USER_AGENT)

    torrents_dir = os.path.expanduser(config.TORRENTS_DIR)
    os.makedirs(torrents_dir, exist_ok=True)
    download_albums_torrents(albums_titles, tracker, torrents_dir)

if __name__ == '__main__':
    main()
