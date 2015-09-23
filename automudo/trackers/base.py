import re
from collections import namedtuple

import requests


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

    def find_torrents_by_keywords(self, keywords,
                                  allow_fancy_releases=None, **kwargs):
        """
        Finds torrents given a keywords list
        and returns their identifiers in the tracker.
        """
        torrents = self._find_torrents_by_keywords(
            keywords, allow_fancy_releases, kwargs
            )
        for torrent in torrents:
            if (self._is_fancy_release(torrent.title) and
                    not allow_fancy_releases):
                continue
            yield torrent

    @staticmethod
    def _has_torrent_content_type(headers):
        """
        Checks if the content type specified in
        the given HTTP headers is of a torrent
        """
        return "application/x-bittorrent" in headers.get('Content-Type', "")

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

    def get_torrent_file_contents(self, torrent_id):
        """
        Returns the contents of the torrent file with the given identifier.
        """
        raise NotImplementedError()
