import requests


class TrackerLoginError(Exception):
    pass


class Tracker(object):
    MAX_LOGIN_ATTEMPTS = 1

    def __init__(self, user_agent):
        self.__session = requests.Session()
        self.__http_headers = {'User-Agent': user_agent}

    def _has_torrent_content_type(self, headers):
        return "application/x-bittorrent" in headers.get('Content-Type', "")

    def _is_authenticated_user_response(self, response):
        raise NotImplementedError()

    def _login(self):
        raise NotImplementedError()

    def _http_request(self, url,
                      method='POST', data=[], cookies=None,
                      headers=dict(), login_if_needed=True):
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
        raise NotImplementedError()

    def get_torrent_file_contents(self, topic_id):
        raise NotImplementedError()
