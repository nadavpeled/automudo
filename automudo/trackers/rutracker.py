from .base import Tracker, TrackerLoginError


class Rutracker(Tracker):
    """
    An implementation of the Tracker interface for rutracker.org
    """
    def __init__(self, username, password, user_agent):
        """
        Initializes the Rutracker object.

        Parameters:
            username - username for the rutracker account
            password - password for the rutracker account
            user_agent - the user agent used for
                         HTTP requests from the tracker
        """
        self.__username = username
        self.__password = password
        super(Rutracker, self).__init__(user_agent)

    @staticmethod
    def _is_authenticated_user_response(response):
        """
            Implementation for Tracker._is_authenticated_user_response .
        """
        return b"logout" in response

    def _login(self):
        """
            Implementation for Tracker._login .
        """
        login_params = {
            'login_username': self.__username,
            'login_password': self.__password,
            'login': "%C2%F5%EE%E4"  # vhod
        }
        url = "http://login.rutracker.org/forum/login.php"
        response = self._http_request(url,
                                      data=login_params,
                                      login_if_needed=False)
        if not self._is_authenticated_user_response(response):
            raise TrackerLoginError("Could not login to rutracker.")

    def find_torrents_by_keywords(self, keywords):
        """
            Implementation for Tracker.find_torrents_by_keywords .
        """
        url = 'http://rutracker.org/forum/tracker.php'
        params = {'nm': " ".join(map('"{}"'.format, keywords))}
        response = self._http_request(url, 'GET', params=params)
        response = response.decode('windows-1251')
        for line in response.splitlines():
            if ('tLink' in line) and ('viewtopic.php' in line):
                yield (line.split('t=')[1].split('"')[0],
                       line.split(">")[1].split("<")[0])

    def get_torrent_file_contents(self, torrent_id):
        """
            Implementation for Tracker.get_torrent_file_contents .
        """
        viewtopic_url_format = "http://rutracker.org/forum/viewtopic.php?t={}"
        referer_header = {'Referer': viewtopic_url_format.format(torrent_id)}
        return self._http_request("http://dl.rutracker.org/forum/dl.php",
                                  'GET',
                                  params={'t': torrent_id},
                                  cookies={'bb_dl': str(torrent_id)},
                                  headers=referer_header)
