import re
import math
import difflib
from collections import namedtuple

import requests

from automudo.music_metadata_databases.base import MusicMetadataDatabase


class TrackerLoginError(Exception):
    """
        Represents tracker login failure.
    """
    pass


TorrentDetails = namedtuple(
    "TorrentDetails",
    ["title", "seeders", "leechers", "size_in_bytes",
     "category", "torrent_id", "tracker_name"]
    )


class Tracker(object):
    """
    An interface representing a tracker of torrents.
    This interface provides functions for searching
    and downloading torrents from the tracker.
    """

    # When inheriting this class, you should define a module-level
    # constant named "name", containing the tracker's name

    def __init__(self, user_agent=None):
        """
        Initializes the Tracker object.
        The user_agent parameter will be the user agent
        provided in HTTP requests to the tracker.
        """
        if not user_agent:
            raise ValueError("user-agent not specified")

        self.__session = requests.Session()
        self.__http_headers = {'User-Agent': user_agent}

    def find_best_torrent_by_keywords(self,
                                      *args,
                                      look_for_discography=False,
                                      **kwargs):
        torrents = self.find_torrents_by_keywords(*args, **kwargs)
        if torrents is None:
            return None

        torrents = list(torrents)
        if not torrents:
            return None

        if look_for_discography:
            filters = [
                self._filter_by_seeders_amount,
                self._filter_higher_sized_torrents
                ]
        else:
            filters = [
                self._filter_lower_sized_torrents,
                self._filter_by_seeders_amount
            ]
        while filters and len(torrents) > 1:
            filtered_torrents = list(filters[0](torrents))
            del filters[0]

            if len(filtered_torrents) > 0:
                # There are torrents that passed the filter.
                torrents = filtered_torrents

        return torrents[0]

    def find_torrents_by_keywords(self, keywords,
                                  allow_fancy_releases=False,
                                  allow_remasters=False,
                                  **kwargs):
        """
        Finds torrents given a keywords list
        and returns their identifiers in the tracker.
        """
        torrents = self._find_torrents_by_keywords(
            keywords, allow_fancy_releases=allow_fancy_releases, **kwargs
            )
        if not allow_fancy_releases:
            torrents = self._filter_non_fancy_torrents(torrents)
        if not allow_remasters:
            torrents = self._filter_non_remasters_torrents(torrents)
        torrents = self._filter_accurate_torrents(torrents, keywords)
        return torrents

    def find_best_discography_torrent(self, artist, *args, **kwargs):
        """
        Finds the best discography torrent for the given album
        and returns its identifier in the tracker.
        """
        raise NotImplementedError()

    def get_torrent_file_contents(self, torrent_id):
        """
        Returns the contents of the torrent file with the given identifier.
        """
        raise NotImplementedError()

    # TORRENT FILTERS:

    @staticmethod
    def _is_fancy_release(title):
        """
        Checks if a torrent's title is for a fancy album release.
        """
        lowercase_title = title.lower()
        return (re.search(r"24([\W\s]+192|[\W\s]*bit)", lowercase_title) or
                re.search(r"180[\W\s]*gram", lowercase_title) or
                "sacd" in lowercase_title or
                "dsd" in lowercase_title or
                "5.1" in lowercase_title or
                "dvd" in lowercase_title or
                "vinyl" in lowercase_title)

    @classmethod
    def _filter_non_fancy_torrents(cls, torrents):
        for torrent in torrents:
            if not cls._is_fancy_release(torrent.title):
                yield torrent

    @staticmethod
    def _filter_non_remasters_torrents(torrents):
        for torrent in torrents:
            if "remaster" not in torrent.title.lower():
                yield torrent

    @staticmethod
    def _filter_accurate_torrents(torrents, keywords):
        for torrent in torrents:
            # Make sure that all of the keywords appear
            # and do not overlap each other.
            torrent_title = MusicMetadataDatabase.normalize_music_description(
                torrent.title
                )
            all_keywords_were_found = True
            searched_string_part = ""
            for keyword in keywords:
                normalized_keyword = \
                    MusicMetadataDatabase.normalize_music_description(keyword)
                if normalized_keyword not in torrent_title:
                    all_keywords_were_found = False
                    break
                keyword_end_index = (torrent_title.find(normalized_keyword) +
                                     len(normalized_keyword))
                searched_string_part += torrent_title[:keyword_end_index]
                torrent_title = torrent_title.replace(
                    normalized_keyword, "", 1
                    )

            if not all_keywords_were_found:
                continue

            # Verify that the shortest prefix that contains all keywords
            # is likely to matche the keywords as a sequence.
            normalized_torrent_title = \
                MusicMetadataDatabase.normalize_music_description(
                    searched_string_part
                    )
            normalized_keywords_string = \
                MusicMetadataDatabase.normalize_music_description(
                    " ".join(keywords)
                    )
            match_ratio = difflib.SequenceMatcher(
                a=normalized_torrent_title,
                b=normalized_keywords_string
                ).ratio()
            if match_ratio > 0.6:
                yield torrent

    @staticmethod
    def _filter_lower_sized_torrents(torrents):
        torrents_sorted_by_size = \
            sorted(torrents, key=lambda t: t.size_in_bytes)

        if len(torrents_sorted_by_size) == 1:
            return torrents_sorted_by_size
        else:
            min_size = torrents_sorted_by_size[0].size_in_bytes
            return [t for t in torrents_sorted_by_size
                    if t.size_in_bytes <= (min_size * 3 / 2)]

    @staticmethod
    def _filter_higher_sized_torrents(torrents):
        torrents_sorted_by_size = \
            sorted(torrents, key=lambda t: t.size_in_bytes,
                   reverse=True)

        if len(torrents_sorted_by_size) == 1:
            return torrents_sorted_by_size
        else:
            end_index = math.ceil(len(torrents_sorted_by_size)/2)
            return torrents_sorted_by_size[:end_index]

    @staticmethod
    def _filter_by_seeders_amount(torrents):
        torrents_sorted_by_seeders = \
            sorted(torrents, key=lambda torrent: torrent.seeders,
                   reverse=True)

        if len(torrents_sorted_by_seeders) == 1:
            return torrents_sorted_by_seeders
        else:
            return torrents_sorted_by_seeders[:-int(len(torrents)/2)]

    # WORK AGAINST THE TRACKER:

    @staticmethod
    def _has_torrent_content_type(headers):
        """
        Checks if the content type specified in
        the given HTTP headers is of a torrent
        """
        return "application/x-bittorrent" in headers.get('Content-Type', "")

    def _is_authenticated_user_response(self, response):
        """
        Checks if the given HTTP response
        is of an authenticated user
        or not (for instance, login page)
        """
        raise NotImplementedError()

    def _login(self):
        """
        Logs in to the tracker.
        """
        raise NotImplementedError()

    def _http_request(self, url, login_if_needed=True, **http_request_args):
        """
        Sends an HTTP request to the tracker and returns the response.
        Automatically performs login if needed.
        Note that the default HTTP method is POST,
        as it tends to be more common in trackers.

        Parameters:
            url - the requested URL
            login_if_needed - optional. should log in if not logged in.
                              defaults to True
            http_request_args - optional. HTTP request arguments
                                (method, headers, data, cookies, ..).

        Returns:
            The HTTP response.

        Raises:
            TrackerLoginError - if login is needed
                                and the login attempts failed.
        """
        method = http_request_args.pop('method', 'POST')
        headers = http_request_args.pop('headers', dict())
        headers.update(self.__http_headers)

        login_attempts = 0
        while True:
            response = self.__session.request(
                method, url,
                headers=headers,
                stream=True,
                **http_request_args
                )

            response_data = b""
            for chunk in response:
                response_data += chunk

            if (self._has_torrent_content_type(response.headers) or
                    self._is_authenticated_user_response(response_data) or
                    not login_if_needed):
                return response_data

            try:
                self._login()
            except TrackerLoginError as exception:
                login_attempts += 1
                if login_attempts == 2:
                    raise exception

    def _find_torrents_by_keywords(self, keywords,
                                   allow_fancy_releases=None, **kwargs):
        """
        Tracker-specific implementation for find_torrents_by_keywords.
        """
        raise NotImplementedError()
