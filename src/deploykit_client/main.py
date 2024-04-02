import sys
import argparse

from deploykit_server import __version__
from deploykit_client import display, handler_deploy, handler_commit, handler_s3
from deploykit_client.config import settings
from deploykit_client.display import UNDERLINE, NORMAL


def main() -> int:
    modules = [handler_deploy, handler_commit, handler_s3]
    parser = argparse.ArgumentParser(prog="deployctl", description="Client for DeployKit, a static website deployment tool")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    subparser = parser.add_subparsers(dest="command", required=True)
    for module in modules:
        module.register_parser(subparser)
    args = parser.parse_args()

    if settings.project.strip() == "":
        display.error(f"Please set your project name as {UNDERLINE}PROJECT{NORMAL} environment variable")
        return 1
    display.success(f"{UNDERLINE}{settings.project}{NORMAL}", prefix="Project")

    for module in modules:
        if args.command == module.__modname__:
            return module.main(args)
    return 1
