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
from automudo.utils.data_sizes import build_data_size_string


TITLES_TO_SKIP_FILE = os.path.join(user_data_dir('Automudo', 'Automudo'),
                                   ".automudo_permanent_skips.csv")


def choose_torrent_for_album(album, tracker, items_per_page):
    """
    Lets the user choose a torrent of the given album in the given tracker.
    Returns a tuple: (user-selection-type, torrent-details).

    Note: might interact with the user for selecting a matching torrent,
          dependening on the user's chosen autoselection mode.
    """
    print("Looking for torrents matching:  {}".format(
        cui.get_printable_string(" - ".join([album.artist, album.title]))
        ))
    available_torrents = tracker.find_torrents_by_keywords(
        [album.artist, album.title]
        )

    def print_torrent_description(result_number, torrent_details):
        print("""
[Torrent {}]
title: {}
size: {}
seeders: {}
leechers: {}
category: {}""".format(
    result_number,
    cui.get_printable_string(torrent_details.title),
    build_data_size_string(torrent_details.size_in_bytes),
    torrent_details.seeders,
    torrent_details.leechers,
    cui.get_printable_string(torrent_details.category)
    ))
        print()

    user_selection_type, chosen_item = cui.let_user_choose_item(
        available_torrents,
        items_per_page,
        print_torrent_description,
        "Please choose a torrent",
        autoselection_modes.AUTOSELECT_IF_ONLY
        )

    torrent_details = None
    if user_selection_type == user_selection_types.ITEM_SELECTED:
        torrent_details = chosen_item
    elif user_selection_type == user_selection_types.NO_ITEMS_TO_SELECT_FROM:
        print("No matching torrents found.")
        print()

    return (user_selection_type, torrent_details)


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
    user_selection_type, torrent_details = choose_torrent_for_album(
        album, tracker, **ui_settings
        )

    if user_selection_type == user_selection_types.ITEM_SELECTED:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            "{} - {} [{}].torrent".format(album.artist, album.title,
                                          torrent_details.torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)

        os.makedirs(torrents_dir, exist_ok=True)
        with open(torrent_file_path, "wb") as torrent_file:
            torrent_file_contents = tracker.get_torrent_file_contents(
                torrent_details.torrent_id
                )
            torrent_file.write(torrent_file_contents)

    return user_selection_type


def get_titles_of_downloaded_albums():
    """
        Returns an iterator of the bookmark titles
        for whom torrents were already downloaded
        in the previous runs of the program.
    """
    try:
        with open(TITLES_TO_SKIP_FILE, "r",
                  encoding="utf-8", newline="") as input_file:
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

    with open(TITLES_TO_SKIP_FILE, "a+",
              encoding="utf-8", newline="") as output_file:
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


def read_selection_field_from_config(config, field_name):
    """
        Reads a selection field as (selected-option, selected-option-settings).
        Assumes the field looks similar to this:
            fruit:
              use: banana
              fruits:
                banana:
                  taste: good
                apple:
                  taste: ok
        (meaning banana is the selected fruit
         and that it's taste field has the value 'good').
    """
    selected = config[field_name]['use']
    all_field_configs = config[field_name]['{}s'.format(field_name)]
    settings_for_selected = all_field_configs[selected]
    if not settings_for_selected:
        settings_for_selected = dict()

    return (selected, settings_for_selected)


def main(config):
    """
        The entry point of the automudo program.
    """
    browser_name, browser_settings = read_selection_field_from_config(
        config, 'browser'
        )
    browser = create_browser(
        browser_name,
        **browser_settings
        )

    database_name, database_settings = read_selection_field_from_config(
        config, 'music_database'
        )
    metadata_database = create_music_metadata_database(
        database_name, user_agent=config['advanced']['user_agent'],
        **database_settings
        )

    tracker_name, tracker_settings = read_selection_field_from_config(
        config, 'tracker'
        )
    tracker = create_tracker(
        tracker_name, user_agent=config['advanced']['user_agent'],
        **tracker_settings
        )

    user_music_bookmarks_titles = browser.get_music_bookmarks_titles()
    already_downloaded_titles = get_titles_of_downloaded_albums()
    titles_to_download = sorted(
        set(user_music_bookmarks_titles) - set(already_downloaded_titles)
        )

    download_albums_by_titles(
        titles_to_download, metadata_database, tracker,
        os.path.expanduser(config['tracker']['output_directory']),
        **config['ui']
        )

if __name__ == '__main__':
    with open("config.yaml", encoding="utf-8") as config_file:
        config_dict = yaml.load(config_file)

    main(config_dict)
