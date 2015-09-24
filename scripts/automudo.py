#! python3
import os
import re
import csv
import itertools

import yaml
from appdirs import user_data_dir

from automudo.ui import cui, user_selection_types
from automudo.browsers.factory import create_browser
from automudo.trackers.factory import create_tracker
from automudo.music_metadata_databases.factory \
    import create_music_metadata_database
from automudo.music_metadata_databases.base import MusicMetadata
from automudo.utils.data_sizes import build_data_size_string


TITLES_TO_SKIP_FILE = os.path.join(user_data_dir('Automudo', 'Automudo'),
                                   ".automudo_permanent_skips.csv")


def find_torrent_for_album(album, tracker,
                           allow_fancy_releases=False, allow_remasters=False,
                           **kwargs):
    """
    Finds a torrent of the given album in the given tracker.
    Returns a tuple: (user-selection-type, torrent-details).
    """
    print("* * * * * Searching Torrent * * * * *")
    print(
        "For:",
        cui.get_printable_string(" - ".join([album.artist, album.title]))
        )
    torrent = tracker.find_best_torrent_by_keywords(
        [album.artist, album.title],
        allow_fancy_releases=allow_fancy_releases,
        allow_remasters=allow_remasters
        )
    if torrent is None:
        print("No matching torrents were found.")
        user_selection_type = user_selection_types.NO_ITEMS_TO_SELECT_FROM
    else:
        print(cui.get_printable_string(
            "Match: {} [{}s/{}l, {}]".format(
                torrent.title, torrent.seeders, torrent.leechers,
                build_data_size_string(torrent.size_in_bytes)
                )
            ))
        user_selection_type = user_selection_types.ITEM_SELECTED

    print()
    return (user_selection_type, torrent)


def download_album_torrent(album, tracker, torrents_dir, **tracker_config):
    """
    Downloads torrent for the music album.

    Parameters:
        album - the metadata of the album to download
        tracker - the tracker to download from
        torrents_dir - the directory into which the torrents will be saved
        tracker_config - the tracker's configuration

    Returns:
        user_selection_types of the torrent selection.
    """
    user_selection_type, torrent_details = find_torrent_for_album(
        album, tracker, **tracker_config
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


def find_album_in_database(title, metadata_database):
    """
        Looks for an album by title in the given metadata database.
        If no matching albums were found, asks the user for help.
        The user may choose to skip.

        Returns:
            (user-selection-type, album-metadata).
    """
    print("* * * * * Searching Album * * * * *")
    print("For:", cui.get_printable_string(title))

    possible_matches = metadata_database.find_album(title)
    # find_album only returns good matches, simply take the first.
    first_match = next(possible_matches, None)
    if first_match is None:
        print("Couldn't find metadata for album. Skipping..")
        user_selection_type = user_selection_types.NO_ITEMS_TO_SELECT_FROM
        album = None
    else:
        user_selection_type = user_selection_types.ITEM_SELECTED
        album, probability = first_match
        print(cui.get_printable_string(
            'Match [{:.2%}]:  {} - {}'.format(
                probability, album.artist, album.title
                )
            ))
    print()
    print()
    return (user_selection_type, album)


def download_albums_by_titles(titles_to_download, metadata_database,
                              tracker, torrents_dir, **tracker_config):
    """
        Downloads torrents for the albums matching the given titles.

        Parameters:
            titles_to_download - titles of tracks/albums to download
            metadata_database - metadata database for searching
                                a matching album
            tracker - the torrents tracker to download the albums from
            torrents_dir - the directory into which the downloaded torrents
                           will be written
            tracker_config - tracker configuration
    """
    file_existed = os.path.exists(TITLES_TO_SKIP_FILE)
    if not file_existed:
        # Make sure that the directory exists
        os.makedirs(os.path.dirname(TITLES_TO_SKIP_FILE), exist_ok=True)

    with open(TITLES_TO_SKIP_FILE, "a+",
              encoding="utf-8", newline="") as output_file:
        skipped_titles_file_writer = csv.DictWriter(
            output_file,
            ['bookmark-title', 'release-id',
             'metadata-database-name', 'reason']
            )
        if not file_existed:
            skipped_titles_file_writer.writeheader()

        for title in titles_to_download:
            user_selection_type, album = find_album_in_database(
                title, metadata_database
                )
            if user_selection_type == user_selection_types.NO_ITEMS_TO_SELECT_FROM:
                skipped_titles_file_writer.writerow({
                    'bookmark-title': title,
                    'release-id': "",
                    'metadata-database-name': metadata_database.name,
                    'reason': "no matching albums"
                    })
                continue  # Skips the torrent downloading as well.

            assert user_selection_type == user_selection_types.ITEM_SELECTED

            user_selection_type = download_album_torrent(
                album, tracker, torrents_dir, **tracker_config
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
    all_configs_field_name = '{}s'.format(field_name)
    selected = config[field_name]['use']
    all_field_configs = config[field_name][all_configs_field_name]

    # Merge settings of the field and the selection
    settings_for_selected = config[field_name]
    del settings_for_selected['use']
    del settings_for_selected[all_configs_field_name]
    if all_field_configs[selected] is not None:
        settings_for_selected.update(all_field_configs[selected])

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
        **tracker_settings
        )

if __name__ == '__main__':
    with open("config.yaml", encoding="utf-8") as config_file:
        config_dict = yaml.load(config_file)

    try:
        main(config_dict)
    except KeyboardInterrupt:
        print("Good bye!")
