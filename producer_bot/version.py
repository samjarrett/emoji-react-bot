import functools
import hashlib
import os


@functools.lru_cache(maxsize=None)
def get_version():
    directory = os.path.dirname(os.path.realpath(__file__))
    version_filename = f"{directory}/../VERSION"

    with open(version_filename, "r") as version_file:
        version = version_file.read().rstrip("\n")

    return version


@functools.lru_cache(maxsize=None)
def get_instance():
    if not os.path.isdir("/var/lib/cloud/data"):
        return None

    with open("/var/lib/cloud/data/instance-id", "r") as instance_id_file:
        instance_id = instance_id_file.read().rstrip("\n")

    return instance_id


def get_instance_hash() -> str:
    instance_id = get_instance()

    if not instance_id:
        return "not-aws"

    return hashlib.sha1(instance_id.encode()).hexdigest()[:6]
