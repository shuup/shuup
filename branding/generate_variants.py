# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shuup Commerce Inc. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import argparse
import os
import re
import subprocess
import tempfile
from PIL import Image


def process_replacements(input_data, replacements):
    data = input_data
    for t_from, t_to in replacements or ():
        data = re.sub(t_from, t_to, data, flags=re.I)
    return data


def update(*args):
    target = args[0]
    for arg in args[1:]:
        target.update(arg)
    return target


class VariantProcessor:
    def __init__(self, output_directory, inkscape):
        self.output_directory = output_directory
        self.inkscape = inkscape
        if not os.path.isdir(self.output_directory):
            os.makedirs(self.output_directory)

    def generate_png(self, info, png_filename, svg_data):
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", suffix=".svg", delete=False) as tmpfile:
            tmpfile.write(svg_data)
            tmpfile.flush()
            command = [
                self.inkscape,
                "--without-gui",
                "-f",
                tmpfile.name,
                "-e",
                png_filename,
                "--export-area-drawing",
                "--export-area-snap",
            ]
            if info.get("background"):
                command.append("--export-background=%s" % info["background"])
            if info.get("dpi"):
                command.append("--export-dpi=%s" % info["dpi"])
            if info.get("width"):
                command.append("--export-width=%s" % info["width"])
            if info.get("height"):
                command.append("--export-height=%s" % info["height"])

            subprocess.check_call(command)

    def process_single_info(self, info):
        with open(info["input"], "r", encoding="utf-8") as input_file:
            input_data = input_file.read()

        png_filename = (info["output"] % info) + ".png"
        png_filename = os.path.join(self.output_directory, png_filename)
        data = process_replacements(input_data, replacements=info.get("replacements"))
        self.generate_png(info, png_filename, data)
        if info.get("format") == "jpg":
            img = Image.open(png_filename)
            jpg_filename = os.path.splitext(png_filename)[0] + ".jpg"
            img.save(jpg_filename, quality=80, progressive=True)
            os.unlink(png_filename)  # Get rid of the PNG
            subprocess.check_call(("jpegoptim", "--strip-all", jpg_filename))

    def process(self, input_files, formats):
        for input_spec in input_files:
            for format in formats:
                info = update(
                    {}, {"base": os.path.splitext(os.path.basename(input_spec["input"]))[0]}, format, input_spec
                )
                self.process_single_info(info)


input_files = [
    {"input": "shuup_logo_only.svg", "width": 1200},
    {"input": "shuup_logo_with_text.svg", "width": 1800},
]

formats = [
    {"output": "%(base)s"},
    {"output": "%(base)s_dark", "replacements": [("#505050", "#ffffff")]},
    {"output": "%(base)s_white_bg", "format": "jpg", "background": "#ffffff"},
    {"output": "%(base)s_black_bg", "format": "jpg", "background": "#000000", "replacements": [("#505050", "#ffffff")]},
]


def cmdline():
    ap = argparse.ArgumentParser(usage="Generate variant images of SVGs.")
    ap.add_argument(
        "--inkscape", dest="inkscape", default="inkscape", help="Path to Inkscape executable", metavar="BIN"
    )
    ap.add_argument("-d", "--dir", dest="output_directory", default="variants", help="Output directory", metavar="DIR")
    args = ap.parse_args()
    vp = VariantProcessor(output_directory=args.output_directory, inkscape=args.inkscape)
    vp.process(input_files, formats)


if __name__ == "__main__":
    cmdline()
