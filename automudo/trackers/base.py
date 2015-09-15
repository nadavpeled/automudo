import requests


class TrackerLoginError(Exception):
    """
        Represents tracker login failure.
    """
    pass


class Tracker(object):
    """
    An interface representing a tracker of torrents.
    This interface provides functions for searching
    and downloading torrents from the tracker.
    """
    MAX_LOGIN_ATTEMPTS = 1

    def __init__(self, user_agent):
        """
        Initializes the Tracker object.
        The user_agent parameter will be the user agent
        provided in HTTP requests to the tracker.
        """
        self.__session = requests.Session()
        self.__http_headers = {'User-Agent': user_agent}

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
                if login_attempts > self.MAX_LOGIN_ATTEMPTS:
                    raise exception

    def find_torrents_by_keywords(self, keywords):
        """
        Finds torrents given a keywords list
        and returns their identifiers in the tracker.
        """
        raise NotImplementedError()

    def get_torrent_file_contents(self, torrent_id):
        """
        Returns the contents of the torrent file with the given identifier.
        """
        raise NotImplementedError()
