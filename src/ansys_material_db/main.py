"""Application entry point for Ansys Material Database."""

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ansys-material-db",
        description="Ansys Thermal Simulation Material Database",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-d", "--database",
        type=str,
        default=None,
        help="Path to SQLite database file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from ansys_material_db.app import run

    return run(args)


if __name__ == "__main__":
    sys.exit(main())