from automudo.trackers.tracker import Tracker, TrackerLoginError


class Rutracker(Tracker):
    def __init__(self, username, password, user_agent):
        self.__username = username
        self.__password = password
        super(Rutracker, self).__init__(user_agent)

    def _is_authenticated_user_response(self, response):
        return b"logout" in response

    def _login(self):
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

    def get_topics_by_title(self, title):
        url = 'http://rutracker.org/forum/tracker.php?nm="{}"+"{}"'
        url = url.format(*title)
        response = self._http_request(url).decode('windows-1251')
        for line in response.splitlines():
            if ('tLink' in line) and ('viewtopic.php' in line):
                yield (line.split('t=')[1].split('"')[0],
                       line.split(">")[1].split("<")[0])

    def get_torrent_file_contents(self, topic_id):
        url = "http://dl.rutracker.org/forum/dl.php?t={}".format(topic_id)
        viewtopic_url_format = "http://rutracker.org/forum/viewtopic.php?t={}"
        referer_header = {'Referer': viewtopic_url_format.format(topic_id)}
        return self._http_request(url,
                                  cookies={'bb_dl': str(topic_id)},
                                  headers=referer_header)
