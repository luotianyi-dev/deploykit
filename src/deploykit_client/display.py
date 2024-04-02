import sys
from typing import Any, Optional, Literal

RED       = "\033[01;91m"
GREEN     = "\033[01;92m"
YELLOW    = "\033[01;93m"
UNDERLINE = "\033[01;04m"
NORMAL    = "\033[00m"

def message(message: str):
    print(message)

def success(message: str, prefix: str = "Success"):
    print(f"{GREEN}{prefix}: {NORMAL}{message}")

def warning(message: str, detail: Optional[str] = None, prefix: str = "Warning"):
    print(f"{YELLOW}{prefix}: {NORMAL}{message}", file=sys.stderr)
    if detail:
        print(detail, file=sys.stderr)
    print()

def error(message: str, detail: Optional[str] = None, prefix: str = "Error"):
    print(f"{RED}{prefix}: {NORMAL}{message}", file=sys.stderr)
    if detail:
        print(detail, file=sys.stderr)
    print()

def http_error(status_code: int, detail: str):
    error(f"HTTP {status_code}", detail)


def table(headers: list[str], data: list[dict[str, Any]]):
    widths = {header: len(header) for header in headers}
    for record in data:
        for key, value in record.items():
            widths[key] = max(widths[key], len(str(value)))
    print("  ".join(header.ljust(widths[header]) for header in headers))
    print("  ".join("-"        * widths[header]  for header in headers))
    for record in data:
        print("  ".join(str(record.get(header, "")).ljust(widths[header]) for header in headers))

def tar_progress(operation: Literal["skip", "add"], path: str):
    if operation == "skip":
        prefix = YELLOW + "[SKIP] "
    if operation == "add":
        prefix = GREEN  + "[ADD]  "
    print(f"TAR: {prefix}{NORMAL}{path}")
