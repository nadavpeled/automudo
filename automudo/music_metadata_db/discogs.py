import requests

from automudo import config
from automudo.music_metadata_db.base import AlbumMetadata, MusicMetadataDB


class DiscogsMetadataDB(MusicMetadataDB):
    @staticmethod
    def _find_album(search_string, master_releases_only):
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
                # remove ", the" from the artist name
                i = result['title'].lower().find(', the')
                if i > 0:
                    j = result['title'].find(' - ', i)
                    result['title'] = result['title'][:i] + result['title'][j:]

                artist, _, title = result['title'].partition(' - ')
                yield AlbumMetadata(artist=artist, title=title,
                                    genres=result.get('style', []),
                                    date=result.get('year', None),
                                    release_id=result['id'],
                                    metadata_db_name="discogs")

            page_number += 1
            if page_number > search_response['pagination']['pages']:
                break  # no more pages
