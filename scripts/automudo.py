import os
import re
import sys

from automudo.ui import cui
from automudo.trackers.rutracker import Rutracker
from automudo.music_bookmarks import get_user_music_bookmarks
from automudo.albums_to_download import get_list_of_albums_to_download
from automudo import config


def get_list_of_topics_to_download(album_titles, tracker):
    for album_title in album_titles:
        print("Looking for torrents matching '{}'..".format(
            cui.get_printable_string(" - ".join(album_title))
            ))
        tracker_topics = tracker.get_topics_by_title(album_title)

        def print_topics_search_result(result_number, result):
            _, topic_title = result
            print("{}. {}".format(
                result_number,
                cui.get_printable_string(topic_title)
                ))
            print()

        try:
            topic = cui.let_user_choose_item(tracker_topics,
                                             config.ITEMS_PER_PAGE,
                                             print_topics_search_result,
                                             "Please choose a torrent",
                                             config.TORRENT_AUTOSELECTION_MODE)
        except cui.NoMoreItemsError:
            print("No matching torrents found.")
            print()
            continue

        if topic:
            topic_id, _ = topic
            yield (topic_id, album_title)


def download_albums_torrents(album_titles, tracker, torrents_dir):
    topics_list = get_list_of_topics_to_download(album_titles, tracker)
    for (topic_id, album_title) in topics_list:
        torrent_file_name = re.sub(
            r'[\/:*?"<>|]', '_',
            " - ".join(album_title) + ' [{}].torrent'.format(topic_id),
            re.UNICODE)
        torrent_file_path = os.path.join(torrents_dir, torrent_file_name)
        with open(torrent_file_path, "wb") as f:
            f.write(tracker.get_torrent_file_contents(topic_id))


def main():
    user_music_bookmarks = get_user_music_bookmarks()
    album_titles = get_list_of_albums_to_download(user_music_bookmarks)

    tracker = Rutracker(config.RUTRACKER_USERNAME,
                        config.RUTRACKER_PASSWORD,
                        config.USER_AGENT)

    download_albums_torrents(album_titles, tracker, config.TORRENTS_DIR)

if __name__ == '__main__':
    main()
