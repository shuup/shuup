# -*- coding: utf-8 -*-
from django.utils import lru_cache
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
import fnmatch

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
                piece = tuple(piece.split("-", 1))
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
            for bit in in_bits:
                if isinstance(bit, tuple):
                    str_bits.append("%s%s-%s" % (prefix, bit[0], bit[1]))
                else:
                    str_bits.append("%s%s" % (prefix, bit))
            bits.extend(sorted(str_bits))

        return ",".join(bits)

    def _test_piece(self, piece, target):
        if target == piece:
            return True
        elif isinstance(piece, tuple):
            min, max = piece[:2]
            if min <= target <= max:
                return True
            if min.isdigit() and max.isdigit() and target.isdigit():
                if int(min) <= int(target) <= int(max):
                    return True
        elif "*" in piece or "?" in piece:
            if fnmatch.fnmatch(target, piece):
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
