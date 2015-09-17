#! python3
import os
import re
import csv

import yaml
from appdirs import user_data_dir

from automudo.ui import cui, user_selection_types, autoselection_modes
from automudo.browsers.factory import create_browser
from automudo.trackers.factory import create_tracker
from automudo.music_metadata_databases.factory import create_music_metadata_database
from automudo.music_metadata_databases.base import MusicMetadata


TITLES_TO_SKIP_FILE = os.path.join(user_data_dir('Automudo', 'Automudo'),
                                   ".automudo_permanent_skips.csv")

# TODO: get this out of here
with open("config.yaml") as config_file:
    config = yaml.load(config_file)


def choose_torrent_for_album(album, tracker, items_per_page,
                             torrents_autoselection_mode):
    """
    Lets the user choose a torrent of the given album in the given tracker.
    Returns a tuple: (user-selection-type, torrent-id).

    Note: might interact with the user for selecting a matching torrent,
          dependening on the user's chosen autoselection mode.
    """
    print("Looking for torrents matching:  {}".format(
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
        items_per_page,
        print_torrent_description,
        "Please choose a torrent",
        torrents_autoselection_mode
        )

    torrent_id = None
    if user_selection_type == user_selection_types.ITEM_SELECTED:
        torrent_id, _ = chosen_item
    elif user_selection_type == user_selection_types.NO_ITEMS_TO_SELECT_FROM:
        print("No matching torrents found.")
        print()

    return (user_selection_type, torrent_id)


def download_album_torrent(album, tracker, torrents_dir, **ui_settings):
    """
    Downloads torrent for the music album.

    Parameters:
        album - the metadata of the album to download
        tracker - the tracker to download from
        torrents_dir - the directory into which the torrents will be saved
        ui_settings - the UI settings from the configuration file

    Returns:
        user_selection_types of the torrent selection.

    Note: might interacts with the user for selecting a matching torrent.
    """
    user_selection_type, torrent_id = choose_torrent_for_album(
        album, tracker, **ui_settings
        )

    if user_selection_type == user_selection_types.ITEM_SELECTED:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            "{} - {} [{}].torrent".format(album.artist, album.title,
                                          torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)

        os.makedirs(torrents_dir, exist_ok=True)
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


def find_album_or_ask_user(title, metadata_database):
    """
        Looks for an album by title in the given metadata database.
        If no matching albums were found, asks the user for help.

        Returns:
            (user-selection-type, album-metadata).
    """
    print("Looking for an album matching:  {}".format(
        cui.get_printable_string(title)
        ))

    album, probability = metadata_database.find_album(title)

    # If the search string is a track name,
    # the matching probability will be lower than expected.
    if ("album" not in title.lower()) and (0.5 < probability < 0.6):
        probability = 0.6

    if (not album) or probability < 0.6:
        print("Couldn't autonomously find a match.")
        artist_name = input(
            "Who is the artist? (Enter - skip, . - permanent skip): "
            )
        if artist_name.strip() == ".":
            return (user_selection_types.PERMANENT_SKIP_REQUESTED, None)
        elif not artist_name.strip():
            return (user_selection_types.SKIPPED_SELECTION, None)
        album_title = input("What is the album title? ")
        print()

        album = MusicMetadata(artist=artist_name, title=album_title,
                              genres=[], date=None, formats=None,
                              release_id="", metadata_database_name="manual")
    else:
        print(cui.get_printable_string(
            'Match [{:.2%}]:  {} - {}'.format(
                probability, album.artist, album.title
                )
            ))

    print()
    return (user_selection_types.ITEM_SELECTED, album)


def download_albums_by_titles(titles_to_download, metadata_database,
                              tracker, torrents_dir, **ui_settings):
    """
        Downloads torrents for the albums matching the given titles.

        Parameters:
            titles_to_download - titles of tracks/albums to download
            metadata_database - metadata database for searching a matching album
            tracker - the torrents tracker to download the albums from
            torrents_dir - the directory into which the downloaded torrents
                           will be written
            ui_settings - the UI settings from the configuration file
    """
    file_existed = os.path.exists(TITLES_TO_SKIP_FILE)
    if not file_existed:
        # Make sure that the directory exists
        os.makedirs(os.path.dirname(TITLES_TO_SKIP_FILE), exist_ok=True)

    with open(TITLES_TO_SKIP_FILE, "a+", newline="") as output_file:
        skipped_titles_file_writer = csv.DictWriter(
            output_file,
            ['bookmark-title', 'release-id', 'metadata-database-name', 'reason']
            )
        if not file_existed:
            skipped_titles_file_writer.writeheader()

        for title in titles_to_download:
            user_selection_type, album = find_album_or_ask_user(
                title, metadata_database
                )
            if user_selection_type == user_selection_types.PERMANENT_SKIP_REQUESTED:
                skipped_titles_file_writer.writerow({
                    'bookmark-title': title,
                    'release-id': "",
                    'metadata-database-name': "",
                    'reason': "permanent skip requested"
                    })
                continue
            elif user_selection_type == user_selection_types.SKIPPED_SELECTION:
                continue  # Skip the torrent downloading as well.

            assert user_selection_type == user_selection_types.ITEM_SELECTED

            user_selection_type = download_album_torrent(
                album, tracker, torrents_dir, **ui_settings
                )
            if user_selection_type == user_selection_types.NO_ITEMS_TO_SELECT_FROM:
                skipped_titles_file_writer.writerow({
                    'bookmark-title': title,
                    'release-id': album.release_id,
                    'metadata-database-name': metadata_database.name,
                    'reason': "no matching torrents"
                    })
            elif user_selection_type == user_selection_types.ITEM_SELECTED:
                # A torrent was chosen.
                skipped_titles_file_writer.writerow({
                    'bookmark-title': title,
                    'release-id': album.release_id,
                    'metadata-database-name': metadata_database.name,
                    'reason': "torrent downloaded"
                    })


def main():
    """
        The entry point of the automudo program.
    """
    browser_name = config['browser']['use']
    browser_settings = config['browser']['browsers'][browser_name]
    browser_settings = browser_settings if browser_settings else dict()
    browser = create_browser(browser_name, **browser_settings)

    database_name = config['music_metadata_database']['use']
    database_settings = config['music_metadata_database']['databases'][database_name]
    database_settings = database_settings if database_settings else dict()
    metadata_database = create_music_metadata_database(
        database_name, user_agent=config['advanced']['user_agent'],
        **config['music_metadata_database']['databases'][database_name]
        )

    tracker_name = config['tracker']['use']
    tracker_settings = config['tracker']['trackers'][tracker_name]
    tracker_settings = tracker_settings if tracker_settings else dict()
    tracker = create_tracker(
        tracker_name, user_agent=config['advanced']['user_agent'],
        **config['tracker']['trackers'][tracker_name]
        )

    user_music_bookmarks_titles = browser.get_music_bookmarks_titles()
    already_downloaded_titles = get_titles_of_downloaded_albums()
    titles_to_download = sorted(
        set(user_music_bookmarks_titles) - set(already_downloaded_titles)
        )

    torrents_autoselection_mode = config['ui']['torrents_autoselection_mode']
    if torrents_autoselection_mode not in autoselection_modes.ALL_MODES:
        print("Invalid torrents autoselection mode.")
        return

    download_albums_by_titles(
        titles_to_download, metadata_database, tracker,
        os.path.expanduser(config['tracker']['output_directory']),
        **config['ui']
        )

if __name__ == '__main__':
    main()
