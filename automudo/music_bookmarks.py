import os
import json
import itertools


def get_user_chrome_bookmarks():
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
            with open(path, "rb") as bookmarks_file:
                bookmarks = json.loads(bookmarks_file.read().decode('utf-8'))
            break
        except IOError:
            continue

    if bookmarks is None:
        raise FileNotFoundError("Chrome's bookmarks file was not found")

    return bookmarks


def parse_chrome_bookmarks(bookmark_node):
    """
        Returns a list of the chrome bookmarks under the given bookmarks node
        in this format:
        [
            (["path", "to", "bookmark"], "<URL>"),
            (["path", "to", "bookmark2"], "<URL>"),
            ...
        ].

        Note: When given the root of the JSON,
              returns the bookmarks from the bookmarks bar.
    """
    if 'roots' in bookmark_node:
        return parse_chrome_bookmarks(bookmark_node['roots']['bookmark_bar'])

    node_name = bookmark_node['name']
    node_type = bookmark_node['type']
    if node_type == 'folder':
        inner_nodes = itertools.chain.from_iterable(
            map(parse_chrome_bookmarks, bookmark_node['children'])
            )
        result = [([node_name] + path, url) for (path, url) in inner_nodes]
        return result
    elif node_type == 'url':
        return [([node_name], bookmark_node['url'])]
    else:
        raise ValueError("Found a chrome bookmark_node node "
                         "whose type is not 'folder' or 'url': " +
                         str(bookmark_node))


def extract_music_bookmarks(all_bookmarks):
    """
        Given a list of bookmarks in the format described in
        parse_chrome_bookmarks, returns a list of the bookmarks
        which contain 'music' as a node in their path
    """
    return [b for b in all_bookmarks if 'music' in map(str.lower, b[0])]


def get_user_music_bookmarks():
    """
        Returns the list of music bookmarks that the user has.

        Assumes the user uses chrome.
        Might be rewrited later on to support other browsers.
    """
    chrome_bookmarks = get_user_chrome_bookmarks()
    parsed_chrome_bookmarks = parse_chrome_bookmarks(chrome_bookmarks)
    return extract_music_bookmarks(parsed_chrome_bookmarks)


def get_user_music_bookmarks_titles():
    """
        Returns the titles that were given to the user's music bookmarks.
    """
    return [bookmark_path[-1]
            for (bookmark_path, bookmark_url)
            in get_user_music_bookmarks()]
