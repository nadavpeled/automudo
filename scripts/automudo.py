#! python3
import os
import re
import csv
import itertools

from automudo import config
from automudo.ui import cui
from automudo.music_bookmarks import get_user_music_bookmarks_titles
from automudo.trackers.rutracker import Rutracker
from automudo.music_metadata_db.discogs import DiscogsMetadataDB


# TODO: Move this file to the user's appdata (or something else in Unix)
DOWNLOADED_ALBUMS_LIST_FILE = os.path.join(config.TORRENTS_DIR,
                                           ".automudo_downloads.csv")


def find_albums_to_download(albums_search_strings, metadata_db):
    """
    Returns a list of tuples in the form (search_string, matching_album)
    for search strings that matched an album in the given database.

    Note: interacts with the user for choosing a correct album name
          from the music metadata databases for each searched album.
    """
    for search_string in albums_search_strings:
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

        try:
            album = cui.let_user_choose_item(
                possible_album_matches,
                config.ITEMS_PER_PAGE,
                print_album_details,
                "Please choose a release",
                config.ALBUM_METADATA_AUTOSELECTION_MODE
                )
        except cui.NoMoreItemsError:
            print("No matching albums found.")
            print()
            continue
        if album:
            yield (search_string, album)


def find_torrents_of_albums(albums, tracker):
    """
    Finds torrents of the given albums in the given tracker.
    Returns a list of tuples in the form (torrent-id, album-title).

    Note: interacts with the user for selecting
          a matching torrent for each album.
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

    Note: interacts with the user for selecting
          a matching torrent for each album.

    Returns:
        Iterator of the albums for whom a torrent was downloaded.
    """
    torrents = find_torrents_of_albums(albums, tracker)
    for (torrent_id, album) in torrents:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            "{} - {} [{}].torrent".format(album.artist, album.title,
                                          torrent_id)
            )
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)
        with open(torrent_file_path, "wb") as torrent_file:
            torrent_file.write(tracker.get_torrent_file_contents(torrent_id))
        yield album


def get_titles_of_downloaded_albums():
    """
        Returns an iterator of the bookmark titles
        for whom torrents were already downloaded
        in the previous runs of the program.
    """
    try:
        with open(DOWNLOADED_ALBUMS_LIST_FILE, "r", newline="") as input_file:
            for row in csv.DictReader(input_file):
                yield row['bookmark-title']
    except IOError:
        pass  # The downloads file does not exist.


def mark_albums_as_downloaded(downloaded_albums, titles_to_albums):
    """
        Writes the titles for whom torrent were downloaded
        to the downloaded albums list file.
    """
    should_write_header = not os.path.exists(DOWNLOADED_ALBUMS_LIST_FILE)

    with open(DOWNLOADED_ALBUMS_LIST_FILE, "a+", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            ['bookmark-title', 'release-id', 'metadata-db-name']
            )
        if should_write_header:
            writer.writeheader()

        for album in downloaded_albums:
            for (title, other_album) in titles_to_albums:
                if other_album == album:
                    writer.writerow(
                        {'bookmark-title': title,
                         'release-id': album.release_id,
                         'metadata-db-name': album.metadata_db_name}
                        )
                    break


def main():
    """
        The entry point of the automudo program.
    """
    # TODO: The discogs and rutracker references should
    #       really be in the configuration file instead.
    metadata_db = DiscogsMetadataDB

    already_downloaded_titles = get_titles_of_downloaded_albums()
    titles_for_download = sorted(
        set(get_user_music_bookmarks_titles()) - set(already_downloaded_titles)
        )

    titles_to_albums = find_albums_to_download(
        titles_for_download,
        metadata_db
        )

    # Note: Needed because there are two independent consumers of the iterable
    titles_to_albums, titles_to_albums2 = itertools.tee(titles_to_albums)
    albums_to_download = (album for (_, album) in titles_to_albums2)

    tracker = Rutracker(config.RUTRACKER_USERNAME,
                        config.RUTRACKER_PASSWORD,
                        config.USER_AGENT)

    torrents_dir = os.path.expanduser(config.TORRENTS_DIR)
    os.makedirs(torrents_dir, exist_ok=True)
    mark_albums_as_downloaded(
        download_albums_torrents(albums_to_download, tracker, torrents_dir),
        titles_to_albums
        )

if __name__ == '__main__':
    main()
