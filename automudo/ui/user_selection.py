class AutoselectModes(object):
    """
        Contains modes for autoselection.

        NEVER_AUTOSELECT - never autoselect.
        AUTOSELECT_IF_ONLY - autoselect if there is only one option.
        ALWAYS_AUTOSELECT - always autoselect.
    """
    NEVER_AUTOSELECT = 0
    AUTOSELECT_IF_ONLY = 1
    ALWAYS_AUTOSELECT = 2


class UserSelectionType(object):
    """
        Contains possible user selection types.
    """
    # The user has selected an item
    ITEM_SELECTED = 0
    # The user requested to skip the current item
    SKIPPED_SELECTION = 1
    # No items to select from
    NO_ITEMS_TO_SELECT_FROM = 2
    # The user has requested permanent skip
    PERMANENT_SKIP_REQUESTED = 3
