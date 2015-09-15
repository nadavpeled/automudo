import re
import requests

from automudo import config
from automudo.music_metadata_db.base import AlbumMetadata, MusicMetadataDB


class DiscogsMetadataDB(MusicMetadataDB):
    """
        A MusicMetadataDB implementation for Discogs.
    """
    @staticmethod
    def _find_album(search_string, master_releases_only):
        """
            Implementation for MusicMetadataDB._find_album .
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

                yield AlbumMetadata(artist=artist, title=title,
                                    genres=result.get('style', []),
                                    date=result.get('year', None),
                                    release_id=result['id'],
                                    metadata_db_name="discogs")

            page_number += 1
            if page_number > search_response['pagination']['pages']:
                break  # No more pages.
