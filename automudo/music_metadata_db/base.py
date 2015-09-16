import re
import difflib
from collections import namedtuple

AlbumMetadata = namedtuple('AlbumMetadata',
                           ['artist', 'title', 'genres',
                            'date', 'formats',
                            'release_id', 'metadata_db_name'])


class MusicMetadataDB(object):
    """
        An interface representing a music metadata database.
        This interface provides functions for searching music metadata.
    """
    # Unwanted keywords that should be removed from search strings.
    _UNWANTED_SEARCH_KEYWORDS = [
        "youtube", "rdio", "grooveshark", "- profile -",
        "from the album", "full album", "debut album", "album",
        "hd", "narrated", "composed", "by", "and", "track", "volume",
        "disc", "cd", "vinyl", "lp", "ep"
        ]

    # The regex pattern matches the keyword if:
    # 1. there is a non-alphabetic character before it
    #    or it's in the beginning of the string
    # 2. there is a non-alphabetic character after it
    #    or it's in the end of the string
    _UNWANTED_KEYWORDS_REGEXES = [
        re.compile(r"(?:(?<=\W)|(?<=^)){}(?=\W|$)".format(k))
        for k in _UNWANTED_SEARCH_KEYWORDS
        ]

    @classmethod
    def find_album(cls, search_string):
        """
            Finds an album in the metadata database matching the search string.

            Parameters:
                search_string - the search string

            Returns:
                (album, probability) tuple.
        """
        normalized_search_string = cls._normalize_album_search_string(
            search_string
            )
        album = cls._find_album(normalized_search_string)
        if album:
            probability = difflib.SequenceMatcher(
                a=normalized_search_string.lower(),
                b=" ".join([album.artist.lower(), album.title.lower()])
                ).ratio()
        else:
            probability = 0
        return album, probability

    @staticmethod
    def _find_album(search_string):
        """
            The DB-specific implementation for find_album.
        """
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

        # Remove comments.
        search_string = re.sub(
            r"(\([^\)]*\)|\({^\}]*\}|\[{^\]*\])", "", search_string
            )

        for regex in cls._UNWANTED_KEYWORDS_REGEXES:
            search_string = regex.sub("", search_string)

        # Replace sequences of spaces and tabs with a single space.
        search_string = re.sub(r"\s+", " ", search_string)

        return search_string.strip()
