class Browser(object):
    """
        An interface representing a browser.
        Provides functions for getting bookmarks from it.
    """

    # When inheriting this class, you should define a module-level
    # constant named "name", containing the browser's name

    def get_all_bookmarks(self):
        """
            Returns all of the user's bookmarks in the browser.
        """
        raise NotImplementedError()

    def get_music_bookmarks(self):
        """
            Returns the user's music bookmarks.
        """
        all_bookmarks = self.get_all_bookmarks()
        return [b for b in all_bookmarks if 'music' in map(str.lower, b[0])]

    def get_music_bookmarks_titles(self):
        """
            Returns the titles that were given to the user's music bookmarks.
        """
        return [bookmark_path[-1]
                for (bookmark_path, bookmark_url)
                in self.get_music_bookmarks()]
