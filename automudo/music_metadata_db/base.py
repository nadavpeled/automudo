import re
from collections import namedtuple

AlbumMetadata = namedtuple('AlbumMetadata',
                           ['artist', 'title', 'genres',
                            'date', 'release_id', 'metadata_db_name'])


class MusicMetadataDB(object):
    """
        An interface representing a music metadata database.
        This interface provides functions for searching music metadata.
    """
    # Non-important keywords that can be removed from search strings.
    _KEYWORDS_TO_REMOVE_FROM_SEARCH_STRING = [
        "youtube", "rdio", "grooveshark", "- profile -",
        "from the album", "full album", "album", "hd",
        "narrated", "composed", "by", "and"
        ]

    # The regex pattern matches the keyword if:
    # 1. there is a non-alphabetic character before it
    #    or it's in the beginning of the string
    # 2. there is a non-alphabetic character after it
    #    or it's in the end of the string
    _REGEXES_OF_KEYWORDS_TO_REMOVE = [
        re.compile(r"(?:(?<=\W)|(?<=^)){}(?=\W|$)".format(k))
        for k in _KEYWORDS_TO_REMOVE_FROM_SEARCH_STRING
        ]

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

    @classmethod
    def _normalize_album_search_string(cls, search_string):
        """
        "Normalizes" an album search string, by performing the following:
        1. lowercasing it
        2. removing useless words from it (album, full album, youtube, ..)
        3. replacing multiple whitespaces with a single whitespace

        Note: No longer removes special characters
              as it causes problems when the artist or album name
              contain special characters.
              The metadata databases can usually handle it.
        """
        search_string = search_string.lower()

        # Remove comments
        search_string = re.sub(
            r"(\([^\)]*\)|\({^\}]*\}|\[{^\]*\])", "", search_string
            )

        for r in cls._REGEXES_OF_KEYWORDS_TO_REMOVE:
            search_string = r.sub("", search_string)

        # Replace sequences of spaces and tabs with a single space
        search_string = re.sub(r"\s+", " ", search_string)

        return search_string.strip()
