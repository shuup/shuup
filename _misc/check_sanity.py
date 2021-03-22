#!/usr/bin/env python3
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
"""
General sanity checker.

Check some common problems in text files of the checkout.

Errors detected by this script:
  * CRLF line-ends
  * Control characters (including TAB) in text files
  * No final end-of-line character at file end present
  * Merge conflict marker present

The output format is

  path/to/file:N:C: S123 Error message
  path/to/file2:M:D: S456 Second error message

where N and M are line numbers, C and D are column numbers, and S123 and
S456 are error codes.

The script will return with exit code 0 if there is were no errors,
otherwise it will return with exit code 1.
"""

import argparse
from sanity_utils import find_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".", help="Root directory (defaults to %(default)s)")
    args = ap.parse_args()
    generated_resources = set()
    paths = find_files(args.root, generated_resources)
    errors = check_sanity_of_files(paths, generated_resources)
    found_errors = False
    for error in errors:
        found_errors = True
        print(error)  # noqa
    if found_errors:
        raise SystemExit(1)


def check_sanity_of_files(paths, ignored_paths):
    for path in paths:
        if path in ignored_paths:
            continue
        for error in check_sanity_of_file(path):
            yield error


def check_sanity_of_file(path):
    reported = set()  # reported codes
    with open(path, "rb") as fp:
        for (num, line) in enumerate(fp, 1):
            for insanity_cls in INSANITY_CLASSES:
                obj = insanity_cls.create_if_present(path, num, line)
                if obj and not (obj.only_once and obj.code in reported):
                    reported.add(obj.code)
                    yield obj


INSANITY_CLASSES = []


def insanity_class(cls):
    if cls not in INSANITY_CLASSES:
        INSANITY_CLASSES.append(cls)
    return cls


class InsanityInLine(object):
    code = "S000"
    insanity = "insane"
    only_once = False
    message_format = "{s.path}:{s.num}:{s.column}: {s.code} {s.insanity}"

    @classmethod
    def create_if_present(cls, path, num, line):
        if cls.check_line(line):
            return cls(path, num, line)
        return None

    def __init__(self, path, num, line):
        self.path = path
        self.num = num
        self.line = line

    @property
    def column(self):
        return 0

    def __str__(self):
        return self.message_format.format(s=self)


@insanity_class
class CrLfInLine(InsanityInLine):
    code = "S101"
    insanity = "CRLF line end"
    only_once = True

    @property
    def column(self):
        return len(self.line) - 1

    @classmethod
    def check_line(cls, line):
        return line.endswith(b"\r\n")


class ControlCharacterInLine(InsanityInLine):
    code = "S102"
    insanity = "Contains control character"
    char = None  # Filled in by the class creation later
    char_description = None  # Filled in by the class creation later

    @classmethod
    def create_if_present(cls, path, num, line):
        charbyte = cls.char

        if line.endswith(b"\r\n") and charbyte == b"\r":
            # Handled in CrLfInLine
            return

        if charbyte in line:
            obj = cls(path, num, line)
            obj.char = charbyte
            return obj

    @property
    def column(self):
        return self.line.index(self.char) + 1

    def __str__(self):
        super_str = super(ControlCharacterInLine, self).__str__()
        return super_str + ": " + self.char_description


@insanity_class
class NoEolInLine(InsanityInLine):
    code = "S103"
    insanity = "End-of-line character missing"

    @property
    def column(self):
        return len(self.line) + 1

    @classmethod
    def check_line(cls, line):
        return not line.rstrip(b"\r").endswith(b"\n")


@insanity_class
class MergeConflictMarkerInLine(InsanityInLine):
    code = "S104"
    insanity = "Merge conflict marker found"

    @property
    def column(self):
        return 1

    @classmethod
    def check_line(cls, line):
        return line.startswith((b"<<<<", b">>>>"))


def register_control_character_insanities():
    for char, description in {
        b"\x00": "NUL",
        b"\x01": "SOH",
        b"\x02": "STX",
        b"\x03": "ETX",
        b"\x04": "EOT",
        b"\x05": "ENQ",
        b"\x06": "ACK",
        b"\x07": "BEL",
        b"\x08": "BS",
        b"\x09": "TAB (HT)",
        # \x0a is not included, since it is LF i.e. '\n'
        b"\x0b": "VT",
        b"\x0c": "FF",
        b"\r": "CR",
        b"\x0e": "SO",
        b"\x0f": "SI",
        b"\x10": "DLE",
        b"\x11": "DC1",
        b"\x12": "DC2",
        b"\x13": "DC3",
        b"\x14": "DC4",
        b"\x15": "NAK",
        b"\x16": "SYN",
        b"\x17": "ETB",
        b"\x18": "CAN",
        b"\x19": "EM",
        b"\x1a": "SUB",
        b"\x1b": "ESC",
        b"\x1c": "FS",
        b"\x1d": "GS",
        b"\x1e": "RS",
        b"\x1f": "US",
    }.items():
        cls = type(
            "%sControlCharacterInLine" % description,
            (ControlCharacterInLine,),
            {"char": char, "char_description": description},
        )
        insanity_class(cls)


register_control_character_insanities()

if __name__ == "__main__":
    main()
