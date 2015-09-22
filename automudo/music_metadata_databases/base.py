import re
import difflib
from collections import namedtuple

MusicMetadata = namedtuple('MusicMetadata',
                           ['artist', 'title', 'genres',
                            'date', 'formats',
                            'release_id', 'metadata_database_name',
                            'tracks'])
TrackMetadata = namedtuple('TrackMetadata', ['title', 'duration'])


class MusicMetadataDatabase(object):
    """
        An interface representing a music metadata database.
        This interface provides functions for searching music metadata.
    """

    # When inheriting this class, you should define a module-level
    # constant named "name", containing the database's name

    # Unwanted keywords that should be removed from search strings.
    # Note that years are removed because the years found in some sources
    # are not the year or release, causing problems in the search.
    _UNWANTED_SEARCH_KEYWORDS = [
        "youtube", "rdio", "grooveshark", "- profile -",
        "from the album", "full album", "album",
        "debut", "self-titled", "self titled",
        "hd", "narrated", "composed", "by",
        "track [a-z]?[0-9]*", "track",
        "volume [a-z]?[0-9]*", "volume",
        "disc [a-z]?[0-9]*", "disc",
        "cd [a-z]?[0-9]*", "cd",
        "vinyl", "lp", "ep",
        "18[8-9][0-9]", "19[0-9][0-9]", "2[0-9][0-9][0-9]"
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

    def find_album(self, search_string):
        """
            Finds an album in the metadata database matching the search string.

            Parameters:
                search_string - the search string

            Returns:
                a list of (album, probability) tuples for possible candidates.
        """
        normalized_search_string = self._normalize_album_search_string(
            search_string
            )
        possible_matches = self._find_album(normalized_search_string)
        return [(album,
                 max(
                     difflib.SequenceMatcher(
                         a=normalized_search_string,
                         b=" ".join([album.artist.lower(),
                                     album.title.lower()])
                         ).ratio(),
                     max([
                         difflib.SequenceMatcher(
                             a=normalized_search_string,
                             b=" ".join([album.artist.lower(),
                                         track.title.lower()])
                             ).ratio()
                         for track in album.tracks] + [0])
                 )) for album in possible_matches]

    def _find_album(self, search_string):
        """
            The database-specific implementation for find_album.
        """
        raise NotImplementedError()

    def _normalize_album_search_string(self, search_string):
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
            r"(\([^\)]*\)|\{[^\}]*\}|\[[^\]]*\])", "", search_string
            )

        for regex in self._UNWANTED_KEYWORDS_REGEXES:
            search_string = regex.sub("", search_string)

        # Remove characters which are not letters or numbers.
        search_string = re.sub(r"(\s|^)[_\W]+(\s|$)", " ", search_string)

        # Replace sequences of spaces and tabs with a single space.
        search_string = re.sub(r"\s+", " ", search_string)

        return search_string.strip()
