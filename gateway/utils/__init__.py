import re
import yaml

from urllib.parse import urlparse
from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n

    return zip_longest(*args, fillvalue=fillvalue)


def camel_to_snake_case(name):
    pre = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)

    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', pre).lower()


def flatten(some_list):
    new_list = []

    for item in some_list:
        if isinstance(item, list):
            new_list.extend(flatten(item))
        else:
            new_list.append(item)

    return new_list


def read_yaml(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def is_url(url):
    try:
        result = urlparse(url)

        return all([result.scheme, result.netloc])
    except (AttributeError, TypeError, ValueError):
        return False
