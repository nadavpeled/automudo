import os
import sys
import string
import itertools

from unidecode import unidecode

from .autoselect_modes import AutoselectModes


class NoMoreItemsError(IndexError):
    """
        There are no more items to select from.
    """
    pass


def get_char_from_terminal():
    """
        Reads a single char from the terminal and returns it
    """
    if os.name.startswith("nt"):  # Windows
        import msvcrt
        return msvcrt.getche().decode('utf-8')
    else:
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def let_user_choose_item(items_iterator, items_per_page,
                         item_printer, prompt, autoselect_mode):
    """
        Lets the user choose an item from a given iterator
        and returns the chosen item.

        Parameters:
            items_iterator - iterator of the items shown to the user
            items_per_page - items shown in each items page
            item_printer - function that prints a given item
            prompt - the user prompt shown after each items page
            autoselect_mode - items autoselection mode

        Returns:
            The chosen item.
            If the user has chosen to skip (avoid) choosing an item,
            returns None.

        Raises:
            NoMoreItemsError - there are no more items that
                               the user can choose from.
    """
    # Note: this program is for the lazy, hench the getch solution
    #       and this assertion, which is needed because of it.
    assert items_per_page < 10

    if not items_iterator:
        raise NoMoreItemsError(
            "let_user_choose_item: there are no items at all"
            )

    page_number = 1
    while True:
        current_items = list(itertools.islice(items_iterator, items_per_page))
        if not current_items:
            raise NoMoreItemsError(
                "let_user_choose_item: there are no more items"
                )

        for item in enumerate(current_items, 1):
            item_printer(*item)

        if ((autoselect_mode == AutoselectModes.AUTOSELECT_IF_ONLY and
             page_number == 1 and len(current_items) == 1) or
                (autoselect_mode == AutoselectModes.ALWAYS_AUTOSELECT)):
            print("Automatically selected (1).")
            print()
            return current_items[0]

        while True:
            print(prompt,
                  "(Enter - 1, n - next, s - skip, q - quit): ",
                  end=" ", flush=True)
            c = get_char_from_terminal().lower()
            print()

            if c == 'n':
                break
            elif c == 's':
                return None
            elif c == 'q':
                sys.exit(0)
            elif c in ['\r', '\n']:
                c = "1"

            if c.isdigit():
                n = int(c)
                if (1 <= n <= len(current_items)):
                    return current_items[n - 1]
                else:
                    print("Out of range..")
        page_number += 1


def get_printable_string(s):
    """
    Returns a printable string which is visually similar to the given string.
    """
    return unidecode(s)
