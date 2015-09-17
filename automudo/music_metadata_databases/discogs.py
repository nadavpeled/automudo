import re

import requests

from .base import MusicMetadata, MusicMetadataDatabase


class DiscogsMetadataDatabase(MusicMetadataDatabase):
    """
        A MusicMetadataDatabase implementation for Discogs.
    """
    name = "discogs"

    def __init__(self, user_agent=None, api_key=None):
        """
            Initializes the DiscogsMetadataDatabase instance.
        """
        if not user_agent:
            raise ValueError("user-agent not specified")
        elif not api_key:
            raise ValueError("API Key not specified")

        self._user_agent = user_agent
        self._api_key = api_key

    def _find_album(self, search_string):
        """
            Implementation for MusicMetadataDatabase._find_album .
        """
        headers = {'User-Agent': self._user_agent}
        params = {'token': self._api_key,
                  'type': "master",
                  'q': search_string,
                  'per_page': 1,
                  'page': 1}
        # The release formats are specified in the order of preference.
        # "" means any format.
        for release_format in ["album", "vinyl", "cd", "lp", ""]:
            params['format'] = release_format
            search_response = requests.get(
                "https://api.discogs.com/database/search",
                params=params, headers=headers
                ).json()

            search_results = search_response['results']
            if search_results:
                break

        if not search_results:
            return None

        result = search_results[0]
        artist, title = result['title'].split(' - ', 1)

        # Remove the string ", the" from the artist name.
        i = artist.lower().find(', the')
        if i > 0:
            artist = artist[:i]

        # Discogs distinguishes between multiple artists
        # with the same name by writing a numeric identifer
        # in parenthesis after the artist name.
        # We don't need this, so we omit it.
        artist = re.sub(r"\s*\([0-9]+\)$", "", artist)

        # When albums with parenthesis in their names are
        # referenced online, the parenthesis part is usually omitted.
        # Therefore, if we don't omit the parenthesis part,
        # searches for albums by the metadata we provide
        # might not be as successful.
        title = re.sub(r"\([^\)]*\)", "", title)

        return MusicMetadata(artist=artist, title=title,
                             genres=result.get('style', None),
                             date=result.get('year', None),
                             formats=result.get('format', None),
                             release_id=result['id'],
                             metadata_database_name=self.name)
