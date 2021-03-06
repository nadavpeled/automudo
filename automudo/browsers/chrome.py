import os
import json
import itertools

from .base import Browser


class ChromeBrowser(Browser):
    """
    A Browser implementation for Chrome.
    """
    name = "chrome"

    def __init__(self):
        """
            Initializes the ChromeBrowser instance.
        """
        super(ChromeBrowser, self).__init__()

    def get_all_bookmarks(self):
        """
            Implementation for Browser.get_all_bookmarks .
        """
        parsed_bookmarks_json = self._get_parsed_bookmarks_json()
        return self._get_all_bookmarks_under_node(parsed_bookmarks_json)

    @staticmethod
    def _get_parsed_bookmarks_json():
        """
            Returns Chrome's (or Chromium's) bookmarks JSON parsed.
            Assumes the user's chrome profile is 'Default'.
        """
        possible_bookmarks_file_paths = map(
            os.path.expanduser,
            ["~/.config/google-chrome/Default/Bookmarks",
             "~/.config/chromium/Default/Bookmarks"]
            )
        if os.name.startswith("nt"):  # Windows
            possible_bookmarks_file_paths = [
                os.path.join(os.getenv('LOCALAPPDATA'),
                             r"Google\Chrome\User Data\Default\Bookmarks")
            ]

        bookmarks = None
        for path in possible_bookmarks_file_paths:
            try:
                with open(path, "r", encoding="utf-8") as bookmarks_file:
                    bookmarks = json.loads(bookmarks_file.read())
                break
            except IOError:
                continue

        if bookmarks is None:
            raise FileNotFoundError("Chrome's bookmarks file was not found")

        return bookmarks

    def _get_all_bookmarks_under_node(self, bookmark_node):
        """
            Returns a list of the chrome bookmarks under the given
            bookmarks node in the following format:
            [
                (["path", "to", "bookmark"], "<URL>"),
                (["path", "to", "bookmark2"], "<URL>"),
                ...
            ].

            Note: When given the root of the JSON,
                  returns the bookmarks from the bookmarks bar.
        """
        if 'roots' in bookmark_node:
            return self._get_all_bookmarks_under_node(
                bookmark_node['roots']['bookmark_bar']
                )

        node_name = bookmark_node['name']
        node_type = bookmark_node['type']
        if node_type == 'folder':
            inner_nodes = itertools.chain.from_iterable(
                map(self._get_all_bookmarks_under_node,
                    bookmark_node['children'])
                )
            result = [([node_name] + path, url) for (path, url) in inner_nodes]
            return result
        elif node_type == 'url':
            return [([node_name], bookmark_node['url'])]
        else:
            raise ValueError("Found a chrome bookmark_node node "
                             "whose type is not 'folder' or 'url': " +
                             str(bookmark_node))
