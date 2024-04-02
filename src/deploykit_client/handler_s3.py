import os
import argparse
import boto3.session
from boto3.s3.transfer import TransferConfig

from deploykit_client import display
from deploykit_client.config import settings
from deploykit_client.display import UNDERLINE, NORMAL, YELLOW, GREEN


__modname__ = "s3"


def register_parser(subparser: argparse.ArgumentParser) -> None:
    parser = subparser.add_parser(__modname__, help="Action for upload local assets to S3-compatible storage")
    parser.add_argument("-b", "--bucket", metavar="<bucket>", help="Bucket name")
    parser.add_argument("-p", "--prefix", metavar="<prefix>", help="Prefix for the files")
    parser.add_argument("-f", "--file", action="append", required=True, metavar="<file>", help="File or directory to upload")

def progress(filename: str, index: int, total: int) -> None:
    text = f"{index + 1}/{total}"
    text_length = len(f"{total}/{total}")
    display.message(f"[{YELLOW}{text:>{text_length}}{NORMAL}] {filename}")

def main(args: argparse.Namespace) -> int:
    session = boto3.session.Session(settings.s3_access_key, settings.s3_secret_key)
    s3 = session.resource(service_name='s3', endpoint_url=settings.s3_endpoint)
    bucket, prefix, includes = args.bucket.strip(), args.prefix.strip('/'), args.file
    display.message(f"Uploading files to {UNDERLINE}{settings.s3_endpoint}/{bucket}/{prefix}{NORMAL}")

    files = []
    for include in includes:
        include = include.strip('/')
        if os.path.isdir(include):
            for root, _, filenames in os.walk(include):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        else:
            files.append(include)
    
    for i, file in enumerate(files):
        progress(file, i, len(files))
        s3.Bucket(bucket).upload_file(file, f"{prefix}/{file}", Config=TransferConfig(
            multipart_threshold=1024 * 25,
            max_concurrency=8,
            use_threads=True))
    display.success(f"Transfered {len(files)} files", prefix="Success")
