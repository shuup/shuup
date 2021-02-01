# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import fnmatch

from django.utils import lru_cache
from django.utils.translation import ugettext_lazy as _

from shuup.utils.django_compat import force_text

PATTERN_SYNTAX_HELP_TEXT = _(
    "Comma-separated values or ranges, e.g. A-Z,10000-19000. "
    "Use exclamation marks to negate (A-Z,!G will not match G)."
)


class Pattern(object):
    def __init__(self, pattern_text):
        """
        Compile a pattern from the given `pattern_text`.

        Patterns are comma-separated atoms of the forms:

        * `*` -- matches anything
        * `text` -- matched directly
        * `min-max` -- inclusive range matched lexicographically OR as integers if possible
        * `wild*` -- wildcards (asterisks and question marks allowed)

        In addition, atoms may be prefixed with `!` to negate them.

        For instance, "10-20,!15" would match all strings (or numbers) between 10 and 20, but not 15.

        :type pattern_text: str
        """
        self.pattern_text = pattern_text
        self.positive_pieces = set()
        self.negative_pieces = set()

        for piece in force_text(self.pattern_text).split(","):
            piece = piece.strip()
            if not piece:
                continue
            if piece.startswith("!"):
                negate = True
                piece = piece[1:].strip()
            else:
                negate = False

            if "-" in piece:
                (min, max) = piece.split("-", 1)
                piece = (min.strip(), max.strip())
            else:
                piece = (piece.strip(), piece.strip())

            if negate:
                self.negative_pieces.add(piece)
            else:
                self.positive_pieces.add(piece)

    def matches(self, target):
        """
        Evaluate this Pattern against the target.

        :type target: str
        :rtype: bool
        """
        target = force_text(target)
        if target in self.negative_pieces:
            return False

        if any(self._test_piece(piece, target) for piece in self.negative_pieces):
            return False

        if "*" in self.positive_pieces or target in self.positive_pieces:
            return True

        return any(self._test_piece(piece, target) for piece in self.positive_pieces)

    def get_alphabetical_limits(self):
        if self.negative_pieces or self.pattern_text == "*":
            return (None, None)
        all_values = set()
        for min_value, max_value in self.positive_pieces:
            all_values.add(min_value)
            all_values.add(max_value)
        if not all_values:
            return (None, None)
        return (min(all_values), max(all_values))

    def as_normalized(self):
        """
        Return the pattern's source text in a "normalized" form.

        :rtype: str
        """
        bits = []
        for prefix, in_bits in [
            ("", self.positive_pieces),
            ("!", self.negative_pieces),
        ]:
            str_bits = []
            for min_value, max_value in in_bits:
                if min_value != max_value:
                    str_bits.append("%s%s-%s" % (prefix, min_value, max_value))
                else:
                    str_bits.append("%s%s" % (prefix, min_value))
            bits.extend(sorted(str_bits))

        return ",".join(bits)

    def _test_piece(self, piece, target):
        """
        Test if piece matches the target value.

        :param piece: Tuple of min and max values
        :type target: str
        :rtype: bool
        """

        min_value, max_value = piece[:2]
        if min_value <= target <= max_value:
            return True

        if min_value.isdigit() and max_value.isdigit() and target.isdigit():
            if int(min_value) <= int(target) <= int(max_value):
                return True

        for value in piece[:2]:
            if "*" in value or "?" in value:
                if fnmatch.fnmatch(target, value):
                    return True


@lru_cache.lru_cache()
def _compile_pattern(pattern):
    return Pattern(pattern)


def pattern_matches(pattern, target):
    """
    Verify that a `target` string matches the given pattern.

    For pattern strings, compiled patterns are cached.

    :param pattern: The pattern. Either a pattern string or a Pattern instance
    :type pattern: str|Pattern
    :param target: Target string to test against.
    :type target: str
    :return: Whether the test succeeded.
    :rtype: bool
    """
    if not isinstance(pattern, Pattern):
        pattern = _compile_pattern(pattern)
    return pattern.matches(target)
