"""Maps the cron schedule string that triggered the workflow to a folder index.
Used only by the GitHub Actions workflow (not imported elsewhere)."""

import sys

CRON_MAP = {
    "30 2 * * *": 0,
    "0 5 * * *": 1,
    "30 7 * * *": 2,
    "0 10 * * *": 3,
    "30 12 * * *": 4,
    "30 14 * * *": 5,
    "30 16 * * *": 6,
}


def main():
    schedule = sys.argv[1] if len(sys.argv) > 1 else ""
    manual = sys.argv[2] if len(sys.argv) > 2 else ""

    if manual.strip() != "":
        idx = int(manual.strip())
    elif schedule in CRON_MAP:
        idx = CRON_MAP[schedule]
    else:
        idx = 0

    print(f"folder_index={idx}")


if __name__ == "__main__":
    main()
