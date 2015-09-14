import re
import sys
import datetime
import itertools
import requests

from automudo.ui import cui
from automudo import config


def normalize_album_search_string(search_string):
    """
    "Normalizes" an album search string, by performing the following:
    1. lowercasing it
    2. removing useless words from it (album, full album, youtube, ..)
    3. removing non-alphanumeric characters
    4. replacing multiple whitespaces with a single whitespace
    """
    search_string = search_string.lower()
    # Remove non important strings and comments
    # (by comments I mean parentheses contents)
    search_string = re.sub(
        r"(\([^\)]*\)|\({^\}]*\}|\[{^\]*\]|youtube|rdio|full album|album)",
        "", search_string
        )
    # Remove anything that is not alphanumeric
    search_string = re.sub(r"[^\w\s]+", "", search_string)
    # Replace sequences of spaces and tabs with a single space
    search_string = re.sub(r"\s+", " ", search_string)
    return search_string.strip()


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


def find_albums_to_download(albums_search_strings):
    """
    Returns a list of albums matching the given search strings.
    Each item in this list is in the form (artist-name, album-name).

    Note: interacts with the user for choosing a correct album name
          from the metadata databases for each searched album
    """
    for search_string in albums_search_strings:
        search_string = normalize_album_search_string(search_string)
        print("------------------------------------------")
        print("Looking for albums matching '{}'..".format(
            cui.get_printable_string(search_string)
            ))
        possible_album_matches = find_possible_album_matches_in_discogs(
            search_string,
            config.MASTER_RELEASES_ONLY
            )

        def print_album_description(result_number, result):
            print("[Album {}]".format(result_number))
            print("title:", cui.get_printable_string(result['title']))
            print("year:", result.get('year', "?"))
            print("genres:", ','.join(result.get('style', ["?"])))
            print()

        try:
            album = cui.let_user_choose_item(
                possible_album_matches,
                config.ITEMS_PER_PAGE,
                print_album_description,
                "Please choose an album",
                config.ALBUM_METADATA_AUTOSELECTION_MODE
                )
        except cui.NoMoreItemsError:
            print("No matching albums found.")
            print()
            continue
        if album:
            yield album['title'].split(" - ")
