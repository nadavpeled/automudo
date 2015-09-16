import os
import sys
import string
import itertools
from collections import OrderedDict

from unidecode import unidecode

from .user_selection import AutoselectModes, UserSelectionType


def get_char_from_terminal():
    """
        Reads a single char from the terminal and returns it
    """
    if os.name.startswith("nt"):  # Windows
        import msvcrt
        c = msvcrt.getwch()
        print(c)
        if c == '\x03':  # Ctrl+C
            raise KeyboardInterrupt()
        return c
    else:
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


def let_user_choose_action(prompt, actions_descriptions,
                           allowed_digits=None):
    """
        Lets the user choose an action from a given set of actions.
        For example, "Would you like to ...? (Y/n)" interactions
        can be implemented as:
            let_user_choose_action("Would you like to ...?",
                                   OrderedDict([('Y', ""),
                                                ('n', "")]))
        You can, of course, put a real description instead of "",
        and then it will be shown to the user in the prompt.

        For numeric selection, you can set allowed_digits
        to be the digits to choose from.
    """
    default_action_char = None
    action_chars_prompt = " ("

    if allowed_digits:
        allowed_digits_as_chars = [str(d) for d in allowed_digits]
        default_action_char = allowed_digits_as_chars[0]
        action_chars_prompt += "Enter - {} / ".format(allowed_digits[0])

    for action_char, description in actions_descriptions.items():
        if action_char.isupper():
            # Make sure that the caller did not define
            # two different action chars.
            assert default_action_char is None
            default_action_char = action_char

        action_chars_prompt += action_char
        if description:
            action_chars_prompt += " - {}".format(description)
        action_chars_prompt += " / "

    # Replace the last " / " with ") ".
    action_chars_prompt = action_chars_prompt[:-3] + "): "

    full_prompt = prompt + action_chars_prompt
    while True:
        print(full_prompt, end="", flush=True)
        action_char = get_char_from_terminal().lower()
        print()

        if action_char in ['\r', '\n']:
            action_char = default_action_char

        if ((action_char in actions_descriptions) or
                (allowed_digits and action_char in allowed_digits_as_chars)):
            return action_char


def let_user_choose_item(items_iterator, items_per_page,
                         item_printer, prompt, autoselect_mode):
    """
        Lets the user choose an item from a given iterator.

        Parameters:
            items_iterator - iterator of the items shown to the user
            items_per_page - items shown in each items page
            item_printer - function that prints a given item
            prompt - the user prompt shown after each items page
            autoselect_mode - items autoselection mode

        Returns:
            A tuple: (user-selection-mode, chosen-item).

        Raises:
            NoItemsError - there are no items that
                           the user can choose from at all.
    """
    items_iterator, items_iterator_backup = itertools.tee(items_iterator)

    were_items_read = False

    page_number = 1
    while True:
        current_items = list(itertools.islice(items_iterator, items_per_page))
        if current_items:
            were_items_read = True
        elif were_items_read:
            action_char = let_user_choose_action("No more options. Repeat?",
                                                 OrderedDict([('y', ""),
                                                              ('N', "")]))
            if action_char == 'y':
                new_iterators = itertools.tee(items_iterator_backup)
                items_iterator, items_iterator_backup = new_iterators
                continue
            else:
                return (UserSelectionType.SKIPPED_SELECTION, None)
        else:
            return (UserSelectionType.NO_ITEMS_TO_SELECT_FROM, None)

        for item in enumerate(current_items, 1):
            item_printer(*item)

        if ((autoselect_mode == AutoselectModes.AUTOSELECT_IF_ONLY and
             page_number == 1 and len(current_items) == 1) or
                (autoselect_mode == AutoselectModes.ALWAYS_AUTOSELECT)):
            print("Automatically selected (1).")
            print()
            return (UserSelectionType.ITEM_SELECTED, current_items[0])

        c = let_user_choose_action(
                prompt,
                OrderedDict([('n', "next"),
                             ('s', "skip")]),
                allowed_digits=range(1, items_per_page + 1))
        if c == 's':
            return (UserSelectionType.SKIPPED_SELECTION, None)
        elif c.isdigit():
            return (UserSelectionType.ITEM_SELECTED,
                    current_items[int(c) - 1])
        else:
            assert c == 'n'
            page_number += 1


def get_printable_string(s):
    """
    Returns a printable string which is visually similar to the given string.
    """
    return unidecode(s)
