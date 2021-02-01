# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2021, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import math
import random

from PIL import Image, ImageDraw

PALATABLE_PALETTES = [
    [(70, 137, 102), (255, 240, 165), (255, 176, 59), (182, 73, 38), (142, 40, 0)],
    [(255, 97, 56), (255, 255, 157), (190, 235, 159), (121, 189, 143), (0, 163, 136)],
    [(34, 83, 120), (22, 149, 163), (172, 240, 242), (243, 255, 226), (235, 127, 0)],
    [(16, 34, 43), (149, 171, 99), (189, 214, 132), (226, 240, 214), (246, 255, 224)],
    [(112, 48, 48), (47, 52, 59), (126, 130, 122), (227, 205, 164), (199, 121, 102)],
    [(4, 191, 191), (202, 252, 216), (247, 233, 103), (169, 207, 84), (88, 143, 39)],
    [(108, 110, 88), (62, 66, 58), (65, 115, 120), (164, 207, 190), (244, 247, 217)],
    [(54, 54, 44), (93, 145, 125), (168, 173, 128), (230, 212, 167), (130, 85, 52)],
    [(255, 128, 0), (255, 217, 51), (204, 204, 82), (143, 179, 89), (25, 43, 51)],
    [(242, 56, 90), (245, 165, 3), (233, 241, 223), (74, 217, 217), (54, 177, 191)],
    [(0, 47, 50), (66, 130, 108), (165, 199, 127), (255, 200, 97), (200, 70, 99)],
    [(230, 70, 97), (255, 166, 68), (153, 138, 47), (44, 89, 79), (0, 45, 64)],
    [(219, 88, 0), (255, 144, 0), (240, 198, 0), (142, 161, 6), (89, 99, 30)],
    [(176, 49, 105), (224, 138, 66), (241, 209, 156), (143, 169, 153), (80, 49, 59)],
    [(168, 20, 97), (91, 23, 71), (14, 25, 43), (101, 113, 159), (190, 169, 169)],
    [(42, 61, 91), (231, 126, 71), (255, 108, 14), (204, 184, 134), (221, 197, 123)]
]


class BaseImageGenerator(object):
    def __init__(self, image, palette, seed):
        """
        :param image: The image to draw on
        :type image: PIL.Image.Image
        :param palette: A list of RGB tuples
        :param seed: Random generator seed
        :type seed: int
        """
        self.seed = seed
        self.image = image
        self.palette = palette

        self.random = random.Random(self.seed)
        self.draw = ImageDraw.Draw(image)
        self.width, self.height = self.image.size
        self.drawers = [getattr(self, n) for n in dir(self) if n.startswith("draw_")]

    def generate(self):  # pragma: no cover
        raise NotImplementedError(
            "Error! Not implemented: `BaseImageGenerator` -> `generate()`. "
            "Should be implemented in subclass, this."
        )

    def draw_circle(self, x, y, w, h, color):
        r = min(w, h) / 2
        self.draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def draw_rectangle(self, x, y, w, h, color):
        wh = w / 2
        hh = h / 2
        self.draw.rectangle((x - wh, y - hh, x + wh, y + hh), fill=color)


class RandomImageGenerator(BaseImageGenerator):
    def generate(self):
        for i in range(self.random.randint(2, 20)):
            self.step()

    def step(self):
        w = int(self.random.uniform(0.1, 0.5) * self.width)
        h = int(self.random.uniform(0.1, 0.5) * self.height)
        x = int(self.random.uniform(0.2, 0.8) * self.width)
        y = int(self.random.uniform(0.2, 0.8) * self.height)
        rgb = self.random.choice(self.palette)
        drawer = self.random.choice(self.drawers)
        drawer(x=x, y=y, w=w, h=h, color=tuple(rgb))


class ModernArtImageGenerator(BaseImageGenerator):
    def generate(self):
        n = self.random.randint(3, 6)
        r = 1 / n
        s = self.random.uniform(0.8, 1)
        for iy in range(n):
            for ix in range(n):
                x = self.width * r * (ix + 0.5)
                y = self.height * r * (iy + 0.5)
                w = self.width * r * s
                h = self.height * r * s
                rgb = self.random.choice(self.palette)
                drawer = self.random.choice(self.drawers)
                drawer(x=x, y=y, w=w, h=h, color=tuple(rgb))
                if self.random.random() < 0.2:
                    drawer(x=x, y=y, w=w * 0.5, h=h * 0.5, color=(255, 255, 255))


class RingImageGenerator(BaseImageGenerator):
    def generate(self):
        n = self.random.randint(3, 9)
        an_delta = (math.pi * 2) / (n - 1)
        wh = self.width / 2
        hh = self.height / 2
        s = self.random.uniform(0.2, 0.5) * min(wh, hh)
        for i in range(n):
            an = i * an_delta
            x = wh + math.cos(an) * wh * 0.8
            y = hh + math.sin(an) * hh * 0.8
            rgb = self.random.choice(self.palette)
            self.draw_circle(x=x, y=y, w=s, h=s, color=tuple(rgb))


generators = [
    RandomImageGenerator,
    ModernArtImageGenerator,
    RingImageGenerator
]


def generate_image(width, height, palette=None, seed=None, supersample=2):
    w, h = width * supersample, height * supersample
    image = Image.new("RGB", (w, h))
    image.paste((255, 255, 255), (0, 0, w, h))
    palette = palette or random.choice(PALATABLE_PALETTES)
    seed = seed or random.randint(0, 1 << 63)
    ig_class = generators[seed % len(generators)]
    ig = ig_class(image=image, palette=palette, seed=seed)
    ig.generate()
    return image.resize((width, height), Image.BILINEAR)
