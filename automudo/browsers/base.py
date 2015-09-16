class Browser(object):
    """
        An interface representing a browser.
        Provides functions for getting bookmarks from it.
    """
    @classmethod
    def get_all_bookmarks(cls):
        """
            Returns all of the user's bookmarks in the browser.
        """
        raise NotImplementedError()

    @classmethod
    def get_music_bookmarks(cls):
        """
            Returns the user's music bookmarks.
        """
        all_bookmarks = cls.get_all_bookmarks()
        return [b for b in all_bookmarks if 'music' in map(str.lower, b[0])]

    @classmethod
    def get_music_bookmarks_titles(cls):
        """
            Returns the titles that were given to the user's music bookmarks.
        """
        return [bookmark_path[-1]
                for (bookmark_path, bookmark_url)
                in cls.get_music_bookmarks()]
