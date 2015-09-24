import re
import datetime

import requests

from .base import MusicMetadata, TrackMetadata, MusicMetadataDatabase


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

        self.__user_agent = user_agent
        self.__api_key = api_key

    @staticmethod
    def _rank_release_formats(formats):
        """
            Ranks the release formats.
            The better the formats, the lower the rank.
        """
        formats = [str.lower(f) for f in formats]
        if "dvd" in formats:
            return 6
        if "unofficial release" in formats:
            return 5
        elif "single" in formats:
            return 4
        elif "compilation" in formats:
            return 3
        elif "album" not in formats:
            return 2
        else:
            return 1

    def _find_album(self, search_string, master_releases, max_results):
        """
            Implementation for MusicMetadataDatabase._find_album .
        """
        headers = {'User-Agent': self.__user_agent}
        params = {'token': self.__api_key,
                  'type': "master" if master_releases else "release",
                  'q': search_string,
                  'per_page': max_results,
                  'page': 1}
        search_response = requests.get(
            "https://api.discogs.com/database/search",
            params=params, headers=headers
            ).json()

        search_results = search_response['results']

        search_results = sorted(
            search_results,
            key=lambda result: self._rank_release_formats(result['format'])
            )

        for result in search_results:
            album_details = requests.get(
                result['resource_url'], headers=headers
                ).json()

            artist = ""
            last_join = ""
            for single_artist in album_details['artists']:
                if last_join:
                    if re.match(r"\w", last_join[0]):
                        artist += " "
                    artist += "{} ".format(last_join)
                artist += single_artist['name']
                last_join = single_artist['join']

            # Remove the string ", the" from the artist name.
            i = artist.lower().find(', the')
            if i > 0:
                artist = artist[:i]

            # Remove "The " from the beginning of the artist name.
            if artist.lower().startswith('the '):
                artist = artist.partition('the ')[2]

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
            title = re.sub(r"\[[^\]]*\]", "", title)
            title = re.sub(r"\{[^\}]*\}", "", title)

            tracks = []
            for track in album_details.get('tracklist', []):
                if track['duration']:
                    minute, second = map(int, track['duration'].split(':'))
                    hour = int(minute / 60)
                    minute = minute % 60
                    duration = datetime.time(hour=hour,
                                             minute=minute,
                                             second=second)
                else:
                    duration = None

                tracks.append(TrackMetadata(title=track['title'],
                                            duration=duration))

            release_date = album_details.get('released', None)
            if release_date:
                release_date = [max(1, int(x))
                                for x in release_date.split("-")]
                while len(release_date) < 3:
                    release_date.append(1)  # Fictive month/day.
                release_date = datetime.date(*release_date)
            yield MusicMetadata(artist=artist, title=title,
                                genres=album_details.get('styles', None),
                                date=release_date,
                                formats=result.get('format', None),
                                release_id=album_details['id'],
                                metadata_database_name=self.name,
                                tracks=tracks)
