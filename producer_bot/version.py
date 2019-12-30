import os
import functools


@functools.lru_cache(maxsize=None)
def get_version():
    directory = os.path.dirname(os.path.realpath(__file__))
    version_filename = f"{directory}/../VERSION"

    with open(version_filename, "r") as f:
        version = f.read().rstrip("\n")

    return version
