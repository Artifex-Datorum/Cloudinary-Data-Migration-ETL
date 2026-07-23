from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError


DEFAULT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".mp4",
    ".mov",
    ".pdf",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate a local media directory to Cloudinary while "
            "preserving its relative folder hierarchy."
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Local source directory containing the assets.",
    )

    parser.add_argument(
        "--destination",
        required=True,
        help="Root destination folder in Cloudinary.",
    )

    parser.add_argument(
        "--folder-mode",
        choices=("dynamic", "fixed"),
        default="dynamic",
        help="Cloudinary product-environment folder mode.",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("migration_manifest.csv"),
        help="CSV file used to record the migration results.",
    )

    parser.add_argument(
        "--extensions",
        nargs="*",
        default=sorted(DEFAULT_EXTENSIONS),
        help="Allowed file extensions, including the leading dot.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permit an existing public ID to be overwritten.",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum upload attempts for each file.",
    )

    return parser.parse_args()


def cloudinary_path(*parts: str) -> str:
    cleaned = [
        part.strip().replace("\\", "/").strip("/")
        for part in parts
        if part and part.strip().strip("/")
    ]
    return str(PurePosixPath(*cleaned)) if cleaned else ""


def discover_assets(
    source: Path,
    extensions: set[str],
) -> list[Path]:
    return sorted(
        file
        for file in source.rglob("*")
        if file.is_file() and file.suffix.lower() in extensions
    )


def build_upload_options(
    *,
    file: Path,
    source: Path,
    destination: str,
    folder_mode: str,
    overwrite: bool,
) -> dict[str, Any]:
    relative_file = file.relative_to(source)
    relative_parent = relative_file.parent.as_posix()
    relative_without_suffix = relative_file.with_suffix("").as_posix()

    destination_folder = cloudinary_path(
        destination,
        relative_parent,
    )

    options: dict[str, Any] = {
        "resource_type": "auto",
        "overwrite": overwrite,
        "invalidate": overwrite,
    }

    if folder_mode == "dynamic":
        options.update(
            {
                "asset_folder": destination_folder,
                "display_name": file.name,
                "public_id": cloudinary_path(
                    destination,
                    relative_without_suffix,
                ),
            }
        )
    else:
        options.update(
            {
                "folder": destination_folder,
                "public_id": file.stem,
            }
        )

    return options


def upload_with_retries(
    *,
    file: Path,
    options: dict[str, Any],
    retries: int,
) -> dict[str, Any]:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            return cloudinary.uploader.upload(
                str(file),
                **options,
            )
        except (CloudinaryError, OSError) as exc:
            last_error = exc
            logging.warning(
                "Attempt %s/%s failed for %s: %s",
                attempt,
                retries,
                file,
                exc,
            )

            if attempt < retries:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Upload failed after {retries} attempts: {file}"
    ) from last_error


def write_manifest_header(writer: csv.DictWriter) -> None:
    writer.writeheader()


def main() -> int:
    args = parse_args()

    if not os.getenv("CLOUDINARY_URL"):
        print(
            "CLOUDINARY_URL is not set. Configure the Cloudinary "
            "credentials before running the migration.",
            file=sys.stderr,
        )
        return 2

    source = args.source.expanduser().resolve()

    if not source.is_dir():
        print(
            f"Source directory not found: {source}",
            file=sys.stderr,
        )
        return 2

    allowed_extensions = {
        extension.lower()
        if extension.startswith(".")
        else f".{extension.lower()}"
        for extension in args.extensions
    }

    assets = discover_assets(
        source,
        allowed_extensions,
    )

    if not assets:
        print("No matching assets were found.", file=sys.stderr)
        return 1

    args.manifest.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    fieldnames = [
        "source_file",
        "relative_path",
        "status",
        "asset_id",
        "public_id",
        "asset_folder",
        "resource_type",
        "format",
        "secure_url",
        "error",
    ]

    successful = 0
    failed = 0

    with args.manifest.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=fieldnames,
        )
        write_manifest_header(writer)

        for index, file in enumerate(assets, start=1):
            relative_path = file.relative_to(source)
            logging.info(
                "[%s/%s] Uploading %s",
                index,
                len(assets),
                relative_path,
            )

            options = build_upload_options(
                file=file,
                source=source,
                destination=args.destination,
                folder_mode=args.folder_mode,
                overwrite=args.overwrite,
            )

            row = {
                "source_file": str(file),
                "relative_path": relative_path.as_posix(),
                "status": "",
                "asset_id": "",
                "public_id": "",
                "asset_folder": "",
                "resource_type": "",
                "format": "",
                "secure_url": "",
                "error": "",
            }

            try:
                result = upload_with_retries(
                    file=file,
                    options=options,
                    retries=args.retries,
                )

                row.update(
                    {
                        "status": "success",
                        "asset_id": result.get("asset_id", ""),
                        "public_id": result.get("public_id", ""),
                        "asset_folder": result.get(
                            "asset_folder",
                            result.get("folder", ""),
                        ),
                        "resource_type": result.get(
                            "resource_type",
                            "",
                        ),
                        "format": result.get("format", ""),
                        "secure_url": result.get(
                            "secure_url",
                            "",
                        ),
                    }
                )
                successful += 1

            except Exception as exc:
                row.update(
                    {
                        "status": "failed",
                        "error": str(exc),
                    }
                )
                failed += 1
                logging.exception(
                    "Migration failed for %s",
                    relative_path,
                )

            writer.writerow(row)
            manifest_file.flush()

    print()
    print(f"Discovered assets: {len(assets)}")
    print(f"Successful uploads: {successful}")
    print(f"Failed uploads: {failed}")
    print(f"Manifest: {args.manifest.resolve()}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
