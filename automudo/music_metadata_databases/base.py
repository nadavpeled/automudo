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
    __UNWANTED_SEARCH_KEYWORDS = [
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
    __UNWANTED_KEYWORDS_REGEXES = [
        re.compile(r"(?:(?<=\W)|(?<=^)){}(?=\W|$)".format(k))
        for k in __UNWANTED_SEARCH_KEYWORDS
        ]

    def find_album(self, search_string):
        """
            Finds an album in the metadata database matching the search string.
            Only returns good matches (>60% probability in a SequenceMatcher).

            Parameters:
                search_string - the search string

            Returns:
                iterable of (album, probability) tuples of good matches.
        """
        normalized_search_string = self.normalize_music_description(
            search_string
            )
        master_releases = self._find_album(normalized_search_string, True)
        all_releases = self._find_album(normalized_search_string, False)

        found_a_good_release = False
        for album in master_releases:
            probability = self._get_album_match_probability(
                normalized_search_string, album
                )
            if probability > 0.6:
                found_a_good_release = True
                yield (album, probability)

        if not found_a_good_release:
            for album in all_releases:
                probability = self._get_album_match_probability(
                    normalized_search_string, album
                    )
                if probability > 0.6:
                    found_a_good_release = True
                    yield (album, probability)

    @staticmethod
    def _get_album_match_probability(normalized_search_string, album):
        album_match_probability = difflib.SequenceMatcher(
            a=normalized_search_string,
            b=" ".join([album.artist.lower(),
                        album.title.lower()])
            ).ratio()
        best_track_match_probability = max(
            [difflib.SequenceMatcher(
                a=normalized_search_string,
                b=" ".join([album.artist.lower(),
                            track.title.lower()])
                ).ratio() for track in album.tracks] + [0])
        return max(album_match_probability, best_track_match_probability)

    @classmethod
    def normalize_music_description(cls, description_string):
        """
        "Normalizes" a music-description string, by performing the following:
        1. lowercasing it
        2. removing useless words from it (album, full album, youtube, ..)
        3. replacing multiple whitespaces with a single whitespace

        Note: No longer removes special characters
              as it causes problems when the artist or album name
              contain special characters.
              The metadata databases can usually handle it.
        """
        description_string = description_string.lower()

        # Remove comments.
        description_string = re.sub(
            r"(\([^\)]*\)|\{[^\}]*\}|\[[^\]]*\])", "", description_string
            )

        for regex in cls.__UNWANTED_KEYWORDS_REGEXES:
            description_string = regex.sub("", description_string)

        # Remove characters which are not letters or numbers.
        description_string = re.sub(r"(\s|^)[_\W]+(\s|$)", " ",
                                    description_string)

        # Replace sequences of spaces and tabs with a single space.
        description_string = re.sub(r"\s+", " ", description_string)

        return description_string.strip()

    def _find_album(self, search_string, master_releases_only):
        """
            The database-specific implementation for find_album.
        """
        raise NotImplementedError()
