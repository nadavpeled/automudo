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

    def _has_torrent_content_type(self, headers):
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

    def _http_request(self, url,
                      method='POST', data=[], cookies=None,
                      headers=dict(), login_if_needed=True):
        """
        Sends an HTTP request to the tracker and returns the response.
        Automatically performs login if needed.
        Note that the default HTTP method is POST,
        as it tends to be more common in trackers.
        """
        headers.update(self.__http_headers)

        login_attempts = 0
        while True:
            response = self.__session.request(
                            method, url,
                            data=data,
                            headers=headers,
                            cookies=cookies,
                            stream=True
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
            except TrackerLoginError as e:
                login_attempts += 1
                if login_attempts > self.MAX_LOGIN_ATTEMPTS:
                    raise e

    def get_topics_by_title(self, title):
        """
        Searches for torrents given a search string
        and returns their identifiers.
        """
        raise NotImplementedError()

    def get_torrent_file_contents(self, topic_id):
        """
        Returns the contents of the torrent file with the given identifier.
        """
        raise NotImplementedError()
