import re
import sys
import datetime
import itertools
import requests

from automudo.ui import cui
from automudo import config


def normalize_bookmark_name(bookmark_name):
    """
    "Normalizes" a bookmark name, by performing the following:
    1. lowercasing it
    2. removing useless words from it (album, full album, youtube, ..)
    3. removing non-alphanumeric characters
    4. replacing multiple whitespaces with a single whitespace
    """
    bookmark_name = bookmark_name.lower()
    # Remove non important strings and comments
    # (by comments I mean parentheses contents)
    bookmark_name = re.sub(
        r"(\([^\)]*\)|\({^\}]*\}|\[{^\]*\]|youtube|rdio|full album|album)",
        "", bookmark_name
        )
    # Remove anything that is not alphanumeric
    bookmark_name = re.sub(r"[^\w\s]+", "", bookmark_name)
    # Replace sequences of spaces and tabs with a single space
    bookmark_name = re.sub(r"\s+", " ", bookmark_name)
    return bookmark_name.strip()


def get_bookmarks_descriptions(music_bookmarks):
    return map(
        lambda bookmark: normalize_bookmark_name(bookmark[0][-1]),
        music_bookmarks
        )


def find_possible_album_matches_in_discogs(search_string,
                                           master_releases_only=True):
    """
    Finds albums whose title is similar to the search string in discogs.

    Parameters:
        search_string - the search string
        master_releases_only - should look for releases other than
                               the very first release of each album

    Returns:
        An iterator of the search results,
        where each result is a dict of album attributes
        (title, date, genre, etc.)
    """
    page_number = 1
    headers = {'User-Agent': config.USER_AGENT}
    params = {
        'token': config.DISCOGS_API_KEY,
        'type': "master" if master_releases_only else "release",
        'format': "album",
        'q': search_string,
        'per_page': config.ITEMS_PER_PAGE,
        'page': 1
        }
    while True:
        search_response = requests.get(
            "https://api.discogs.com/database/search",
            params=params, headers=headers
            ).json()

        search_results = search_response['results']
        for result in search_results:
            i = result['title'].lower().find(', the')
            if i > 0:
                j = result['title'].find(' - ', i)
                result['title'] = result['title'][:i] + result['title'][j:]

            yield result

        page_number += 1
        if page_number > search_response['pagination']['pages']:
            break  # no more pages


def get_list_of_albums_to_download(music_bookmarks):
    """
    Returns a list of albums to download given the user's music bookmarks.
    Each item in this list is in the form (artist-name, album-name).

    Note: interacts with the user for choosing a correct album name
          from the metadata databases for each music bookmark
    """
    for bookmark_description in get_bookmarks_descriptions(music_bookmarks):
        print("------------------------------------------")
        print("Looking for albums matching '{}'..".format(
            cui.get_printable_string(bookmark_description)
            ))
        possible_album_matches = find_possible_album_matches_in_discogs(
            bookmark_description,
            config.MASTER_RELEASES_ONLY
            )

        def print_album_search_result(result_number, result):
            print("[Album {}]".format(result_number))
            print("title:", cui.get_printable_string(result['title']))
            print("year:", result.get('year', "?"))
            print("genres:", ','.join(result.get('style', ["?"])))
            print()

        try:
            album = cui.let_user_choose_item(
                possible_album_matches,
                config.ITEMS_PER_PAGE,
                print_album_search_result,
                "Please choose an album",
                config.ALBUM_METADATA_AUTOSELECTION_MODE
                )
        except cui.NoMoreItemsError:
            print("No matching albums found.")
            print()
            continue
        if album:
            yield album['title'].split(" - ")
