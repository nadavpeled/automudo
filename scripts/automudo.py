#! python3
import os
import re
import csv
import itertools

from automudo import config
from automudo.ui import cui
from automudo.ui.user_selection import UserSelectionType
from automudo.browsers.chrome import ChromeBrowser
from automudo.trackers.rutracker import Rutracker
from automudo.music_metadata_db.discogs import DiscogsMetadataDB


# TODO: Move this file to the user's appdata (or something else in Unix)
TITLES_TO_SKIP_FILE = os.path.join(config.TORRENTS_DIR,
                                   ".automudo_permanent_skips.csv")


def choose_matching_album(search_string, metadata_db):
    """
    Lets the user choose an album matching the given search string
    in the given metadata database.
    Returns a tuple: (user-selection-type, album-metadata).

    Note: might interact with the user for selecting a matching album,
          dependening on the user's chosen autoselection mode.
    """
    print("------------------------------------------")
    print("Looking for music releases matching '{}'..".format(
        cui.get_printable_string(search_string)
        ))
    possible_album_matches = metadata_db.find_album(
        search_string,
        config.MASTER_RELEASES_ONLY
        )

    def print_album_details(result_number, album):
        print("[Release {}]".format(result_number))
        print("artist:", cui.get_printable_string(album.artist))
        print("title:", cui.get_printable_string(album.title))
        print("date:", album.date if album.date else "?")
        print("genres:", cui.get_printable_string(",".join(album.genres)
                                                  if album.genres
                                                  else "?"))
        print("format:", cui.get_printable_string(",".join(album.formats)
                                                  if album.formats
                                                  else "?"))
        print()

    user_selection_type, album = cui.let_user_choose_item(
        possible_album_matches,
        config.ITEMS_PER_PAGE,
        print_album_details,
        "Please choose a release",
        config.ALBUM_METADATA_AUTOSELECTION_MODE
        )

    if user_selection_type == UserSelectionType.NO_ITEMS_TO_SELECT_FROM:
        print("No matching albums found.")
        print()

    return (user_selection_type, album)


def choose_torrent_for_album(album, tracker):
    """
    Lets the user choose a torrent of the given album in the given tracker.
    Returns a tuple: (user-selection-type, torrent-id).

    Note: might interact with the user for selecting a matching torrent,
          dependening on the user's chosen autoselection mode.
    """
    print("Looking for torrents matching '{}'..".format(
        cui.get_printable_string(" - ".join([album.artist, album.title]))
        ))
    available_torrents = tracker.find_torrents_by_keywords(
        [album.artist, album.title]
        )

    def print_torrent_description(result_number, result):
        _, torrent_title = result
        print("{}. {}".format(
            result_number,
            cui.get_printable_string(torrent_title)
            ))
        print()

    user_selection_type, chosen_item = cui.let_user_choose_item(
        available_torrents,
        config.ITEMS_PER_PAGE,
        print_torrent_description,
        "Please choose a torrent",
        config.TORRENT_AUTOSELECTION_MODE
        )

    torrent_id = None
    if user_selection_type == UserSelectionType.ITEM_SELECTED:
        torrent_id, _ = chosen_item
    elif user_selection_type == UserSelectionType.NO_ITEMS_TO_SELECT_FROM:
        print("No matching torrents found.")
        print()

    return (user_selection_type, torrent_id)


def download_album_torrent(album, tracker, torrents_dir):
    """
    Downloads torrent for the music album.

    Parameters:
        album - the metadata of the album to download
        tracker - the tracker to download from
        torrents_dir - the directory into which the torrents will be saved

    Returns:
        UserSelectionType of the torrent selection.

    Note: might interacts with the user for selecting a matching torrent.
    """
    user_selection_type, torrent_id = choose_torrent_for_album(album, tracker)

    if album:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            "{} - {} [{}].torrent".format(album.artist, album.title,
                                          torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)
        with open(torrent_file_path, "wb") as torrent_file:
            torrent_file.write(tracker.get_torrent_file_contents(torrent_id))

    return user_selection_type


def get_titles_of_downloaded_albums():
    """
        Returns an iterator of the bookmark titles
        for whom torrents were already downloaded
        in the previous runs of the program.
    """
    try:
        with open(TITLES_TO_SKIP_FILE, "r", newline="") as input_file:
            for row in csv.DictReader(input_file):
                yield row['bookmark-title']
    except IOError:
        pass  # The downloads file does not exist.


def download_albums_by_titles(titles_to_download,
                              metadata_db, metadata_db_name,
                              tracker, torrents_dir):
    """
        Downloads torrents for the albums matching the given titles.

        Parameters:
            titles_to_download - titles of tracks/albums to download
            metadata_db - metadata database for searching a matching album
            metadata_db_name - the name of the metadata database
            tracker - the torrents tracker to download the albums from
            torrents_dir - the directory into which the downloaded torrents
                           will be written
    """
    should_write_header = not os.path.exists(TITLES_TO_SKIP_FILE)
    with open(TITLES_TO_SKIP_FILE, "a+", newline="") as output_file:
        skipped_titles_file_writer = csv.DictWriter(
            output_file,
            ['bookmark-title', 'release-id', 'metadata-db-name', 'reason']
            )
        if should_write_header:
            skipped_titles_file_writer.writeheader()

        for title in titles_to_download:
            user_selection_type, album = choose_matching_album(
                title, metadata_db
                )
            if user_selection_type == UserSelectionType.NO_ITEMS_TO_SELECT_FROM:
                skipped_titles_file_writer.writerow({
                    'bookmark-title': title,
                    'release-id': "",
                    'metadata-db-name': "",
                    'reason': "no matching albums"
                    })
            elif user_selection_type == UserSelectionType.ITEM_SELECTED:
                user_selection_type = download_album_torrent(
                    album, tracker, torrents_dir
                    )
                if user_selection_type == UserSelectionType.NO_ITEMS_TO_SELECT_FROM:
                    skipped_titles_file_writer.writerow({
                        'bookmark-title': title,
                        'release-id': album.release_id,
                        'metadata-db-name': metadata_db_name,
                        'reason': "no matching torrents"
                        })
                elif user_selection_type == UserSelectionType.ITEM_SELECTED:
                    # A torrent was chosen.
                    skipped_titles_file_writer.writerow({
                        'bookmark-title': title,
                        'release-id': album.release_id,
                        'metadata-db-name': metadata_db_name,
                        'reason': "torrent downloaded"
                        })


def main():
    """
        The entry point of the automudo program.
    """
    # TODO: The discogs, rutracker and Chrome references
    #       should really be in the configuration file instead.
    metadata_db_name = "discogs"
    metadata_db = DiscogsMetadataDB
    browser = ChromeBrowser
    tracker = Rutracker(config.RUTRACKER_USERNAME,
                        config.RUTRACKER_PASSWORD,
                        config.USER_AGENT)

    torrents_dir = os.path.expanduser(config.TORRENTS_DIR)
    os.makedirs(torrents_dir, exist_ok=True)

    user_music_bookmarks_titles = browser.get_music_bookmarks_titles()
    already_downloaded_titles = get_titles_of_downloaded_albums()
    titles_to_download = sorted(
        set(user_music_bookmarks_titles) - set(already_downloaded_titles)
        )

    download_albums_by_titles(titles_to_download,
                              metadata_db, metadata_db_name,
                              tracker, torrents_dir)

if __name__ == '__main__':
    main()
