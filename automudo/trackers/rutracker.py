import re
import html

from .base import Tracker, TrackerLoginError, TorrentDetails
from ..utils.data_sizes import parse_data_size_string
from ..utils.html_parse import find_html_tags_by_type, search_html_tag_by_type, get_text


class Rutracker(Tracker):
    """
    An implementation of the Tracker interface for rutracker.org
    """
    name = "rutracker"

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

    def _is_authenticated_user_response(self, response):
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

    def _extract_torrents_from_html(self, html_string):
        """
            Gets an HTTP response from the server as a string
            and extracts TorrentDetails for each torrent in it.
            returns an iterator of the TorrentDetails-s.
        """
        html_string = html_string.partition(' id="tor-tbl">')[2]
        torrents_table_body = search_html_tag_by_type("tbody", html_string)
        no_results = False
        for row in find_html_tags_by_type("tr", torrents_table_body):
            for cell in find_html_tags_by_type("td", row):
                if "Не найдено" in cell:
                    no_results = True
                    break
                cell = html.unescape(cell)
                if "t-title" in cell:  # Torrent title.
                    title = get_text(cell)
                elif "f-name" in cell:  # Forum title.
                    category = get_text(cell)
                elif "tr-dl" in cell:  # Download link + torrent size.
                    torrent_id = int(
                        re.search(r'dl.php\?t=(.*?)">', cell).group(1)
                        )
                    size_string = search_html_tag_by_type("a", cell)
                    size_string = size_string.rpartition(" ")[0]

                    size_in_bytes = parse_data_size_string(size_string)
                elif "seed" in cell:  # Seeders amount.
                    seeders = int(search_html_tag_by_type("b", cell))
                elif cell.startswith("<b>"):  # Leechers amount.
                    leechers = int(search_html_tag_by_type("b", cell))
            if not no_results:
                yield TorrentDetails(title=title,
                                     seeders=seeders, leechers=leechers,
                                     size_in_bytes=size_in_bytes,
                                     category=category, torrent_id=torrent_id,
                                     tracker_name=self.name)

    def find_torrents_by_keywords(self, keywords):
        """
            Implementation for Tracker.find_torrents_by_keywords .

            Note: does not look past the first search page.
        """
        url = 'http://rutracker.org/forum/tracker.php'
        params = {
            'nm': " ".join(map('"{}"'.format, keywords)),
            'o': "10"  # Sort by seeders amount.
            }
        response = self._http_request(url, 'GET', params=params)
        response = response.decode('windows-1251')

        yield from self._extract_torrents_from_html(response)

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
