import os
import re
import sys

from automudo import config
from automudo.ui import cui
from automudo.music_bookmarks import get_user_music_bookmarks_titles
from automudo.music_metadata_db.discogs import DiscogsMetadataDB
from automudo.trackers.rutracker import Rutracker


def find_albums_to_download(albums_search_strings, metadata_db):
    """
    Returns a list of albums matching the given search strings
    in the given music metadata database.

    Note: interacts with the user for choosing a correct album name
          from the music metadata databases for each searched album
    """
    for search_string in albums_search_strings:
        print("------------------------------------------")
        print("Looking for albums matching '{}'..".format(
            cui.get_printable_string(search_string)
            ))
        possible_album_matches = metadata_db.find_album(
            search_string,
            config.MASTER_RELEASES_ONLY
            )

        def print_album_details(result_number, album):
            print("[Album {}]".format(result_number))
            print("artist:", cui.get_printable_string(album.artist))
            print("title:", cui.get_printable_string(album.title))
            print("date:", album.date if album.date else "?")
            print("genres:", ",".join(album.genres) if album.genres else "?")
            print()

        try:
            album = cui.let_user_choose_item(
                possible_album_matches,
                config.ITEMS_PER_PAGE,
                print_album_details,
                "Please choose an album",
                config.ALBUM_METADATA_AUTOSELECTION_MODE
                )
        except cui.NoMoreItemsError:
            print("No matching albums found.")
            print()
            continue
        if album:
            yield album


def find_torrents_of_albums(albums, tracker):
    """
    Finds torrents of the given albums in the given tracker.
    Returns a list of tuples in the form (torrent-id, album-title).

    Note: interacts with the user for selecting
          a matching torrent for each album
    """
    for album in albums:
        print("Looking for torrents matching '{}'..".format(
            cui.get_printable_string(" - ".join([album.artist, album.title]))
            ))
        available_torrents = tracker.find_torrents_by_keywords([album.artist,
                                                                album.title])

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
            yield (torrent_id, album)


def download_albums_torrents(albums, tracker, torrents_dir):
    """
    Downloads torrents for music albums.

    Parameters:
        albums - the metadata of the albums to download
        tracker - the tracker to download from
        torrents_dir - the directory into which the torrents will be saved
    """
    torrents = find_torrents_of_albums(albums, tracker)
    for (torrent_id, album) in torrents:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            "{} - {} [{}].torrent".format(album.artist, album.title,
                                          torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)
        with open(torrent_file_path, "wb") as f:
            f.write(tracker.get_torrent_file_contents(torrent_id))


def main():
    albums = find_albums_to_download(get_user_music_bookmarks_titles(),
                                     DiscogsMetadataDB)

    tracker = Rutracker(config.RUTRACKER_USERNAME,
                        config.RUTRACKER_PASSWORD,
                        config.USER_AGENT)

    torrents_dir = os.path.expanduser(config.TORRENTS_DIR)
    os.makedirs(torrents_dir, exist_ok=True)
    download_albums_torrents(albums, tracker, torrents_dir)

if __name__ == '__main__':
    main()
