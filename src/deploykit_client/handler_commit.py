import argparse
from pytz import timezone
from datetime import datetime

from deploykit_client import display
from deploykit_client.config import settings
from deploykit_client.session import Session, SessionError
from deploykit_client.display import UNDERLINE, NORMAL

__modname__ = "commit"
session = Session()


def register_parser(subparser: argparse.ArgumentParser) -> None:
    parser = subparser.add_parser(__modname__, help="Actions related to commits")
    action_parser = parser.add_subparsers(dest="action", required=True)
    action_parser.add_parser("list", help="List commits")

    delete_action = action_parser.add_parser("delete", help="Delete a commit and related deployment")
    delete_action.add_argument("commit_hash", metavar="<commit-sha1>", help="Commit hash to delete")
    delete_action.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

def list_commits() -> int:
    try:
        commits = session.request("GET", f"projects/{settings.project}/commits")["commits"]
    except SessionError:
        display.error("Could not list commits")
        return 1
    for commit in commits:
        commit["created_at"] = datetime.fromtimestamp(
            commit["created_at"],
            timezone(settings.timezone)
        ).isoformat()
    display.table(["commit_hash", "deployment_id", "created_at"], commits)
    return 0

def delete_commit(commit_hash: str, confirmed: bool) -> int:
    if not confirmed:
        display.warning(f"Deleting a commit is will {UNDERLINE}ALSO DELETE{NORMAL} the related deployment. Do you want to continue? (yes/no): ")
        if input().lower() != "yes":
            display.error("User aborted the action")
            return 2
    try:
        response = session.request("DELETE", f"projects/{settings.project}/commits/{commit_hash}")
    except SessionError:
        display.error("Could not delete commit")
        return 1
    display.error(str(response), prefix="Deleted")
    return 0

def main(args: argparse.Namespace) -> int:
    if args.action == "list":
        return list_commits()
    if args.action == "delete":
        return delete_commit(commit_hash=args.commit_hash, confirmed=args.yes)
    return 1
