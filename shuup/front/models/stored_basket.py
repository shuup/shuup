from django.utils.crypto import get_random_string


def generate_key():
    return get_random_string(32)
