import re

import requests

from automudo import config
from .base import AlbumMetadata, MusicMetadataDB


class DiscogsMetadataDB(MusicMetadataDB):
    """
        A MusicMetadataDB implementation for Discogs.
    """
    @staticmethod
    def _find_album(search_string):
        """
            Implementation for MusicMetadataDB._find_album .
        """
        headers = {'User-Agent': config.USER_AGENT}
        params = {
            'token': config.DISCOGS_API_KEY,
            'type': "master",
            'q': search_string,
            'per_page': 1,
            'page': 1
            }

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

        return AlbumMetadata(artist=artist, title=title,
                             genres=result.get('style', None),
                             date=result.get('year', None),
                             formats=result.get('format', None),
                             release_id=result['id'],
                             metadata_db_name="discogs")
