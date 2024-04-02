import io
import os
import tarfile
import argparse
from pytz import timezone
from typing import Optional
from datetime import datetime
from zstandard import ZstdCompressor

from deploykit_client import display
from deploykit_client.config import settings
from deploykit_client.session import Session, SessionError
from deploykit_client.display import UNDERLINE, NORMAL, YELLOW, GREEN


__modname__ = "deploy"
session = Session()


def register_parser(subparser: argparse.ArgumentParser) -> None:
    parser = subparser.add_parser(__modname__, help="Actions related to deployments")
    action_parser = parser.add_subparsers(dest="action", required=True)
    action_parser.add_parser("list", help="List deployments")

    delete_action = action_parser.add_parser("delete", help="Delete a deployment")
    delete_action.add_argument("deployment_id", metavar="<deployment-id>", help="Deployment ID to delete")
    delete_action.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    upload_action = action_parser.add_parser("upload", help="Upload a deployment")
    upload_action.add_argument("-c", "--commit", metavar="<commit-hash>", help="Commit hash to deploy")
    upload_action.add_argument("-f", "--file", nargs=2, metavar="<file> <arcname>", action="append", required=True, help="Directory or file to be uploaded")
    upload_action.add_argument("--switch", action="store_true", help="Switch 'current' to this deployment")

    switch_action = action_parser.add_parser("switch", help="Switch 'current' to a deployment")
    switch_action.add_argument("deployment_id", metavar="<deployment-id>", help="Deployment ID to switch to")

def list_deployments() -> int:
    try:
        deployments = session.request("GET", f"projects/{settings.project}/deployments")["deployments"]
    except SessionError:
        display.error("Could not list deployments")
        return 1
    for deployment in deployments:
        deployment["created_at"] = datetime.fromtimestamp(
            deployment["created_at"],
            timezone(settings.timezone)
        ).isoformat()
    display.table(["deployment_id", "created_at"], deployments)
    return 0

def delete_deployment(deployment_id: str, confirmed: bool) -> int:
    if not confirmed:
        display.warning(f"Will delete the deployment on server {UNDERLINE}permanently{NORMAL}. Do you want to continue? (yes/no): ")
        display.warning(f"Will delete the deployment on server {UNDERLINE}permanently{NORMAL}. Do you want to continue? (yes/no): ")
        if input().lower() != "yes":
            display.error("User aborted the action")
            return 2
    try:
        response = session.request("DELETE", f"projects/{settings.project}/deployments/{deployment_id}")
    except SessionError:
        display.error("Could not delete deployment")
        return 1
    display.error(str(response), prefix="Deleted")
    return 0

def upload_deployment(files: list[list[str]], commit: Optional[str], switch: bool) -> int:
    display.message(f"Uploading deployment with commit={UNDERLINE}{commit}{NORMAL}")
    display.message(f"Current directory: {UNDERLINE}{os.getcwd()}{NORMAL}")
    with io.BytesIO() as tar_stream, io.BytesIO() as zstd_stream:
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            for file, arcname in files:
                if file.startswith("..") or os.path.isabs(file):
                    display.tar_progress("skip", file)
                    continue
                display.tar_progress("add", file)
                tar.add(os.path.abspath(file), arcname=arcname, recursive=True)
        tar_size = tar_stream.tell()
        tar_stream.seek(0)
        display.message(f"Compressing...")
        compressor = ZstdCompressor(level=19)
        compressor.copy_stream(tar_stream, zstd_stream, read_size=tar_size)
        zstd_size = zstd_stream.tell()
        zstd_stream.seek(0)
        display.success(f"{tar_size} -> {zstd_size} bytes", prefix="Compressed")
        try:
            params = {"commit_hash": commit} if commit else None
            file = {"upload": zstd_stream}
            response = session.request("POST", f"projects/{settings.project}/deployments", params=params, files=file)
        except SessionError:
            display.error("Could not upload deployment")
            return 1
        display.success(str(response), prefix="Uploaded")
    if switch:
        return switch_deployment(response["deployment_id"])
    return 0

def switch_deployment(deployment_id: str) -> int:
    try:
        response = session.request("PATCH", f"projects/{settings.project}/current", params={"deployment_id": deployment_id})
    except SessionError:
        display.error(f"Could not switch deployment {YELLOW}{deployment_id}{NORMAL}")
        return 1
    display.success(str(response))
    display.message(f"Switched to deployment {GREEN}{UNDERLINE}{deployment_id}{NORMAL}")
    return 0

def main(args: argparse.Namespace) -> int:
    if args.action == "list":
        return list_deployments()
    if args.action == "upload":
        return upload_deployment(files=args.file, commit=args.commit, switch=args.switch)
    if args.action == "delete":
        return delete_deployment(deployment_id=args.deployment_id, confirmed=args.yes)
    if args.action == "switch":
        return switch_deployment(deployment_id=args.deployment_id)
    return 1
