from .rutracker import Rutracker

SUPPORTED_TRACKERS = [Rutracker]


def create_tracker(tracker_name, **kwargs):
    """
        Finds the class that inherits Tracker
        and has the given tracker name,
        and initializes an object of it using kwargs.
    """
    for tracker in SUPPORTED_TRACKERS:
        if tracker.name == tracker_name:
            return tracker(**kwargs)
    return KeyError(
        "Tracker {} not found. Supported trackers are: {}".format(
            tracker_name,
            ", ".join(tracker.name for tracker in SUPPORTED_TRACKERS)
            ))
