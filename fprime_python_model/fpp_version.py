from packaging.version import Version

MIN_FPP_VERSION = Version("3.1.0a10")


def check_version(to_check: str, msg: str) -> None:
    if Version(to_check) < MIN_FPP_VERSION:
        raise ValueError(f"{msg}\nMinimum supported: {MIN_FPP_VERSION}")
