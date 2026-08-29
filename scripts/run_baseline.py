from __future__ import annotations

import argparse
import json

from patchproof.workflow.baseline_runner import (
    run_baseline,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case",
        required=True,
    )

    args = parser.parse_args()

    result = run_baseline(
        args.case
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
