import re
import datetime

import requests

from .base import MusicMetadata, MusicMetadataDatabase


class DiscogsMetadataDatabase(MusicMetadataDatabase):
    """
        A MusicMetadataDatabase implementation for Discogs.
    """
    name = "discogs"

    def __init__(self, user_agent=None, api_key=None, max_results=None):
        """
            Initializes the DiscogsMetadataDatabase instance.
        """
        if not user_agent:
            raise ValueError("user-agent not specified")
        elif not api_key:
            raise ValueError("API Key not specified")

        self._user_agent = user_agent
        self._api_key = api_key
        self._max_results = max_results if max_results else 3

    def _find_album(self, search_string):
        """
            Implementation for MusicMetadataDatabase._find_album .
        """
        headers = {'User-Agent': self._user_agent}
        params = {'token': self._api_key,
                  'type': "master",
                  'q': search_string,
                  'per_page': self._max_results,
                  'page': 1}
        search_response = requests.get(
            "https://api.discogs.com/database/search",
            params=params, headers=headers
            ).json()

        search_results = search_response['results']
        search_results = sorted(
            search_results,
            key=lambda result:
                (lambda formats:
                     4 if "single" in formats
                     else 3 if "compilation" in formats
                     else 2 if "album" not in formats
                     else 1
                )([str.lower(f) for f in result['format']])
            )

        for result in search_results:
            album_details = requests.get(
                result['resource_url'], headers=headers
                ).json()

            artist = ""
            last_join = ""
            for single_artist in album_details['artists']:
                if last_join:
                    if(re.match("\w", last_join[0])):
                        artist += " "
                    artist += "{} ".format(last_join)
                artist += single_artist['name']
                last_join = single_artist['join']

            # Remove the string ", the" from the artist name.
            i = artist.lower().find(', the')
            if i > 0:
                artist = artist[:i]

            # Discogs distinguishes between multiple artists
            # with the same name by writing a numeric identifer
            # in parenthesis after the artist name.
            # We don't need this, so we omit it.
            artist = re.sub(r"\s*\([0-9]+\)$", "", artist)

            title = album_details['title']
            # When albums with parenthesis in their names are
            # referenced online, the parenthesis part is usually omitted.
            # Therefore, if we don't omit the parenthesis part,
            # searches for albums by the metadata we provide
            # might not be as successful.
            title = re.sub(r"\([^\)]*\)", "", title)

            release_date = result.get('released', None)
            if release_date:
                release_date = datetime.date(*('-'.split(release_date)))
            yield MusicMetadata(artist=artist, title=title,
                                genres=result.get('styles', None),
                                date=release_date,
                                formats=result.get('format', None),
                                release_id=result['id'],
                                metadata_database_name=self.name)