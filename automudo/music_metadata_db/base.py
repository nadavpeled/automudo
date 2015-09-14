import re
from collections import namedtuple

AlbumMetadata = namedtuple('AlbumMetadata',
                           ['artist', 'title', 'genres', 'date'])


class MusicMetadataDB(object):
    """
        An interface representing a music metadata database.
        This interface provides functions for searching music metadata.
    """
    @classmethod
    def find_album(cls, search_string, master_releases_only=True):
        """
            Finds albums in the DB whose title is similar
            to the search string in discogs.

            Parameters:
                search_string - the search string
                master_releases_only - should look for releases other than
                                       the very first release of each album

            Returns:
                An iterator of the search results (as AlbumMetadata-s).
        """
        yield from cls._find_album(
            cls._normalize_album_search_string(search_string),
            master_releases_only
            )

    @staticmethod
    def _find_album(search_string, master_releases_only):
        raise NotImplementedError()

    @staticmethod
    def _normalize_album_search_string(search_string):
        """
        "Normalizes" an album search string, by performing the following:
        1. lowercasing it
        2. removing useless words from it (album, full album, youtube, ..)
        3. removing non-alphanumeric characters
        4. replacing multiple whitespaces with a single whitespace
        """
        search_string = search_string.lower()
        # Remove non important strings and comments
        # (by comments I mean parentheses contents)
        search_string = re.sub(
            r"(\([^\)]*\)|\({^\}]*\}|\[{^\]*\]|youtube|rdio|full album|album)",
            "", search_string
            )
        # Remove anything that is not alphanumeric
        search_string = re.sub(r"[^\w\s]+", "", search_string)
        # Replace sequences of spaces and tabs with a single space
        search_string = re.sub(r"\s+", " ", search_string)
        return search_string.strip()
