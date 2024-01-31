import sys


def is_test() -> bool:
    """determine if system is in testing mode"""
    args = sys.argv[1:2]
    return args and args[0] == "test"
