# -*- coding: utf-8 -*-
# This file is part of Shuup.
#
# Copyright (c) 2012-2019, Shoop Commerce Ltd. All rights reserved.
#
# This source code is licensed under the OSL-3.0 license found in the
# LICENSE file in the root directory of this source tree.
import random

ADJECTIVES = (
    "abundant", "adorable", "agreeable", "alive", "ancient",
    "angry", "beautiful", "better", "bewildered", "big", "bitter",
    "black", "blue", "boiling", "brave", "breeze", "brief", "broad",
    "broken", "bumpy", "calm", "careful", "chilly", "chubby", "clean",
    "clever", "clumsy", "cold", "colossal", "cooing", "cool", "creepy",
    "crooked", "cuddly", "curly", "curved", "damaged", "damp", "dead",
    "deafening", "deep", "defeated", "delicious", "delightful", "dirty",
    "drab", "dry", "dusty", "eager", "early", "easy", "elegant",
    "embarrassed", "empty", "faint", "faithful", "famous", "fancy",
    "fast", "fat", "few", "fierce", "filthy", "flaky", "flat", "fluffy",
    "freezing", "fresh", "full", "gentle", "gifted", "gigantic",
    "glamorous", "gray", "greasy", "great", "green", "grumpy",
    "handsome", "happy", "heavy", "helpful", "helpless", "high",
    "hissing", "hollow", "hot", "huge", "icy", "immense", "important",
    "inexpensive", "itchy", "jealous", "jolly", "juicy", "kind",
    "large", "late", "lazy", "light", "little", "lively", "long",
    "loose", "loud", "low", "magnificent", "mammoth", "many", "massive",
    "melodic", "melted", "miniature", "modern", "mushy", "mysterious",
    "narrow", "nervous", "nice", "noisy", "numerous", "nutritious",
    "obedient", "obnoxious", "odd", "old", "old-fashioned", "orange",
    "panicky", "petite", "plain", "powerful", "prickly", "proud",
    "puny", "purple", "purring", "quaint", "quick", "quiet", "rainy",
    "rapid", "raspy", "red", "relieved", "repulsive", "rich", "rotten",
    "round", "salty", "scary", "scrawny", "screeching", "shallow",
    "short", "shy", "silly", "skinny", "slow", "small", "sparkling",
    "sparse", "square", "steep", "sticky", "straight", "strong",
    "substantial", "sweet", "swift", "tall", "tart", "tasteless",
    "teeny", "teeny-tiny", "tender", "thankful", "thoughtless",
    "thundering", "tiny", "ugliest", "uneven", "uninterested",
    "unsightly", "uptight", "vast", "victorious", "voiceless", "warm",
    "weak", "wet", "whispering", "white", "wide", "wide-eyed", "witty",
    "wooden", "worried", "wrong", "yellow", "young", "yummy", "zealous",
)

NOUNS = (
    "acoustics", "action", "activity", "actor", "advice",
    "aftermath", "afternoon", "afterthought", "airplane", "airport",
    "alarm", "anger", "animal", "answer", "apparel", "apple",
    "appliance", "arithmetic", "arm", "army", "aunt", "badge", "bait",
    "ball", "balloon", "banana", "baseball", "basket", "basketball",
    "bat", "bath", "battle", "bead", "beam", "bean", "beast", "bed",
    "bedroom", "beef", "beetle", "beggar", "beginner", "believe",
    "bike", "bird", "birthday", "bomb", "book", "boot", "border",
    "boundary", "boy", "brain", "branch", "bread", "breakfast", "brick",
    "brother", "brush", "bubble", "bucket", "bun", "bushes", "butter",
    "cabbage", "cable", "cactus", "cake", "calculator", "calendar",
    "camp", "can", "cannon", "cap", "caption", "car", "carpenter",
    "cast", "cat", "cattle", "cave", "celery", "cellar", "cemetery",
    "cent", "channel", "cherries", "cherry", "chicken", "children",
    "chin", "circle", "clam", "class", "cloth", "clover", "club",
    "coach", "coast", "cobweb", "coil", "corn", "cow", "cracker",
    "crate", "crayon", "cream", "creator", "creature", "crib", "crook",
    "crow", "crowd", "crown", "cub", "cup", "dad", "daughter", "day",
    "deer", "desk", "dime", "dinner", "dirt", "dock", "doctor", "dog",
    "doll", "donkey", "downtown", "dress", "drug", "drum", "dust",
    "earthquake", "education", "eggnog", "elbow", "eye", "face",
    "family", "fan", "fang", "father", "faucet", "feast", "feather",
    "feet", "field", "fifth", "fight", "finger", "fireman", "flag",
    "flavor", "flesh", "flock", "flower", "fog", "food", "frame",
    "friction", "frog", "fruit", "fuel", "furniture", "galley", "game",
    "gate", "geese", "ghost", "giraffe", "girl", "glove", "glue",
    "goldfish", "goose", "governor", "grade", "grain", "grandfather",
    "grandmother", "grape", "grass", "guide", "guitar", "gun", "hair",
    "haircut", "hall", "hat", "health", "heart", "heat", "hen", "hill",
    "hobbies", "holiday", "home", "honey", "hook", "hope", "horn",
    "horse", "hose", "hot", "hydrant", "icicle", "idea", "income",
    "island", "jail", "jam", "jar", "jeans", "jellyfish", "joke",
    "judge", "juice", "kiss", "kite", "kitten", "laborer", "lace",
    "ladybug", "lake", "lamp", "language", "lawyer", "lettuce", "light",
    "linen", "loaf", "lock", "locket", "lumber", "lunch", "lunchroom",
    "magic", "maid", "mailbox", "man", "map", "marble", "mask", "meal",
    "meat", "men", "mice", "milk", "minister", "mint", "mitten", "mom",
    "money", "month", "moon", "morning", "mother", "mountain", "music",
    "name", "nest", "north", "nose", "notebook", "number", "oatmeal",
    "ocean", "owl", "pail", "pan", "pancake", "parent", "park",
    "partner", "passenger", "patch", "pear", "pen", "pencil", "pest",
    "pet", "pickle", "picture", "pie", "pig", "plane", "plant",
    "plantation", "plastic", "playground", "pleasure", "plot", "pocket",
    "poison", "police", "pollution", "popcorn", "pot", "queen",
    "quicksand", "quiet", "quilt", "rabbit", "railway", "rain",
    "rainstorm", "rake", "rat", "recess", "reward", "riddle", "rifle",
    "river", "road", "robin", "rock", "room", "rose", "route", "sack",
    "sail", "scale", "scarecrow", "scarf", "scene", "scent", "sea",
    "seashore", "seed", "shape", "sheet", "shoe", "shop", "show",
    "sidewalk", "sink", "sister", "skate", "slave", "sleet", "smoke",
    "snail", "snake", "snow", "soap", "soda", "sofa", "son", "song",
    "space", "spark", "spoon", "spot", "spy", "squirrel", "stage",
    "star", "station", "step", "stew", "stove", "stranger", "straw",
    "stream", "street", "string", "sugar", "suit", "summer", "sun",
    "sweater", "swing", "table", "tank", "team", "temper", "tent",
    "territory", "test", "texture", "thread", "thrill", "throat",
    "throne", "tiger", "title", "toad", "toe", "toes", "toothbrush",
    "toothpaste", "town", "trail", "tramp", "tray", "treatment", "tree",
    "trick", "trip", "tub", "turkey", "twig", "uncle", "underwear",
    "vacation", "van", "vase", "vegetable", "veil", "vein", "vest",
    "visitor", "volcano", "volleyball", "voyage", "water", "wealth",
    "weather", "week", "wheel", "wilderness", "wing", "winter", "wish",
    "woman", "wood", "wool", "wren", "wrench", "wrist", "writer",
    "yard", "year", "zebra",
)


def random_title(second_adj_chance=0.3, prefix="", suffix=""):
    bits = [random.choice(ADJECTIVES)]
    if random.random() < second_adj_chance:
        bits.append(random.choice(ADJECTIVES))
    bits.append(random.choice(NOUNS))
    text = (prefix + ' '.join(bits) + suffix)
    return text.title()
