<p align="center">
  <img
    src="https://upload.wikimedia.org/wikipedia/commons/b/b0/Cloudinary_logo_blue_0720_2x.png"
    alt="Cloudinary Logo"
    width="420"
  >
</p>

<h1 align="center">Cloudinary Data Migration ETL</h1>

This repository provides a reusable framework for migrating digital media assets into **Cloudinary** while preserving their original folder hierarchy. It is designed as a general data-migration project rather than a solution tied to one particular source.

The workflow can be used with assets extracted from:

* a GitHub, GitLab, or other Git repository;
* a local computer folder;
* a network drive or shared filesystem;
* a synchronised Google Drive, OneDrive, or Dropbox folder;
* an exported object-storage directory;
* a mounted cloud-storage location;
* any other source that can be represented as files and folders on the local filesystem.

The project applies an **Extract, Transform, Load, and Validate** methodology. Assets are first obtained from the source, filtered and prepared in a staging area, uploaded to Cloudinary, and finally checked through counts, logs, and sample validation.

The recommended one-time migration method uses the **Cloudinary Command Line Interface**, whose `upload_dir` command can upload an entire local directory while maintaining its subfolder structure. A Python ETL alternative is also documented for migrations requiring custom file selection, deterministic public IDs, manifests, retry logic, or more detailed auditing.

<h1 align="center"><i>Why Migrate Assets to Cloudinary?</i></h1>

Migrating media assets to Cloudinary centralises their storage, management, optimisation, and delivery within a platform designed specifically for images, videos, and other digital media. Instead of maintaining large files directly inside source repositories, local folders, or disconnected storage locations, organisations can keep their application code and documentation lightweight while delivering media through secure, scalable URLs.

The principal advantages include:

* **Centralised asset management:** Images, videos, documents, and related files can be organised, searched, tagged, reviewed, and managed from a unified Media Library.
* **Preserved logical organisation:** Existing directory structures can be reproduced as Cloudinary asset folders, making migrated collections easier to navigate.
* **Automatic optimisation:** Cloudinary can dynamically optimise formats, quality, dimensions, and compression for different devices and delivery contexts.
* **Faster global delivery:** Assets can be served through Cloudinary's content-delivery infrastructure rather than directly from a source repository or local server.
* **Responsive transformations:** Applications can request resized, cropped, reformatted, or otherwise transformed variants without storing numerous duplicate files.
* **Reduced repository size:** Moving large media collections outside Git repositories keeps source-control projects lighter and easier to clone, maintain, and deploy.
* **Consistent delivery URLs:** Cloudinary provides secure HTTPS URLs that can be used in websites, dashboards, documentation, notebooks, and applications.
* **Improved automation:** Uploads, transformations, tagging, metadata assignment, and lifecycle operations can be integrated into ETL pipelines, CI/CD workflows, and application back ends.
* **Better scalability:** New assets and derived versions can be managed without redesigning the original filesystem or repeatedly copying files between environments.
* **Migration auditability:** CLI logs, Python manifests, returned asset identifiers, and validation counts make the migration process easier to verify and document.

The migration should still be planned carefully. Folder mode, public-ID strategy, credential security, overwrite behaviour, supported formats, storage quotas, and validation requirements should be confirmed before production assets are transferred.

<h1 align="center"><i>Project Objectives</i></h1>

The principal objectives of this project are to:

* migrate media assets into Cloudinary in a controlled and repeatable manner;
* preserve the logical hierarchy of source folders;
* avoid uploading irrelevant files such as Git metadata, notebooks, or documentation;
* protect Cloudinary API credentials throughout the process;
* test the connection with a single asset before beginning the full migration;
* validate that the number of successfully migrated assets matches the expected source count;
* record migration results in a manifest for future review;
* remove temporary credentials and staging data after completion;
* provide a method that can be reused for different repositories, directories, and media collections.

<h1 align="center"><i>ETL Architecture</i></h1>

```text
Source Repository, Folder, Drive, or Export
                    │
                    ▼
             1. EXTRACT
      Clone, copy, mount, or download
                    │
                    ▼
            2. TRANSFORM
  Filter extensions, validate files, preserve
  relative paths, create staging directories,
       and prepare migration metadata
                    │
                    ▼
               3. LOAD
      Upload assets through Cloudinary CLI
        or the Cloudinary Python SDK
                    │
                    ▼
             4. VALIDATE
 Compare counts, inspect logs, open sample assets,
   confirm folders, and record Cloudinary results
                    │
                    ▼
              5. CLOSE
 Remove temporary credentials, staging folders,
          test assets, and migration keys
```

<h1 align="center"><i>Supported Migration Methods</i></h1>

## 1. Cloudinary CLI Directory Migration

This is the recommended approach for a complete one-time migration of an existing folder hierarchy.

```powershell
cld upload_dir `
    --folder "Target-Cloudinary-Folder" `
    --exclude-dir-name `
    --concurrent_workers 8 `
    "C:\Path\To\Prepared-Assets"
```

This method is suitable when:

* the source has already been downloaded or synchronised locally;
* the existing folder structure should be reproduced in Cloudinary;
* extensive per-file transformations are not required;
* a fast and repeatable migration is preferred.

## 2. Python ETL Migration

The Python method is suitable when the migration requires:

* extension allowlists or denylists;
* custom public-ID generation;
* folder-name mapping;
* tags or contextual metadata;
* per-file exception handling;
* retry logic;
* a CSV or JSON migration manifest;
* deterministic asset paths;
* selective reprocessing of failed files.

## 3. Cloudinary Media Library Upload

For small or occasional migrations, an entire folder can be dragged into the Cloudinary Media Library. This provides a browser-based alternative when Python or the CLI cannot be installed.

The CLI and Python approaches remain preferable when repeatability, logging, filtering, and auditability are important.

<h1 align="center"><i>Quick Start with the Cloudinary CLI</i></h1>

## 1. Obtain the source assets

A Git repository can be cloned with:

```powershell
git clone https://github.com/USERNAME/REPOSITORY.git
```

For a non-Git source, copy, synchronise, download, or mount the required folder locally.

## 2. Create a virtual environment

```powershell
py -m venv "$env:USERPROFILE\CloudinaryMigrationEnv"
& "$env:USERPROFILE\CloudinaryMigrationEnv\Scripts\Activate.ps1"
```

## 3. Install the Cloudinary CLI

```powershell
python -m pip install --upgrade pip
python -m pip install cloudinary-cli
```

Confirm the installation:

```powershell
cld --version
```

## 4. Configure Cloudinary temporarily

Create a dedicated migration API key in Cloudinary rather than using a permanent production key.

```powershell
$secureCloudinaryUrl = Read-Host `
    "Paste the complete Cloudinary URL" `
    -AsSecureString

$env:CLOUDINARY_URL = [System.Net.NetworkCredential]::new(
    "",
    $secureCloudinaryUrl
).Password

Remove-Variable secureCloudinaryUrl
```

The value pasted at the prompt must follow this format:

```text
cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Verify the target product environment:

```powershell
cld config
```

## 5. Test one file

```powershell
$testSource = Join-Path $env:TEMP "cloudinary-migration-test"

Remove-Item $testSource `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

New-Item `
    -ItemType Directory `
    -Path $testSource |
    Out-Null

Copy-Item `
    "C:\Path\To\One\Test\Asset.png" `
    $testSource

cld upload_dir `
    --folder "_migration_test" `
    --exclude-dir-name `
    --concurrent_workers 1 `
    "$testSource"
```

Open the `_migration_test` folder in Cloudinary and confirm that the asset is readable.

## 6. Upload the complete staging directory

```powershell
cld upload_dir `
    --folder "Target-Cloudinary-Folder" `
    --exclude-dir-name `
    --concurrent_workers 8 `
    "C:\Path\To\Prepared-Assets"
```

## 7. Close the connection

```powershell
Remove-Item Env:CLOUDINARY_URL `
    -ErrorAction SilentlyContinue

deactivate
```

After validating the complete migration, disable the temporary migration API key in Cloudinary.

<h1 align="center"><i>Python ETL Example</i></h1>

The following example recursively scans a source directory, filters supported media types, preserves each relative folder path, uploads the assets, and writes a CSV manifest.

It supports both Cloudinary folder modes:

* `dynamic`, used by current Cloudinary environments;
* `fixed`, retained for legacy environments.

```python
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
```

An example execution is:

```powershell
python scripts\migrate_assets.py `
    --source "C:\Path\To\Source-Assets" `
    --destination "Migrated-Assets" `
    --folder-mode dynamic `
    --manifest "manifests\migration_manifest.csv"
```

<h1 align="center"><i>Credential Security</i></h1>

The Cloudinary API secret must never be:

* committed to Git;
* written directly into a Python script;
* inserted into a public notebook;
* included in screenshots;
* pasted into issue trackers;
* printed in migration logs;
* shared through chat messages.

A `.gitignore` file should contain:

```gitignore
.env
.env.*
!.env.example

CloudinaryMigrationEnv/
.venv/
venv/

logs/
manifests/*.csv

__pycache__/
*.py[cod]

Relational-Dataset-Images-PNG-Only/
staging/
```

An `.env.example` file may contain placeholders only:

```dotenv
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

<h1 align="center"><i>Folder Modes</i></h1>

Current Cloudinary environments normally use **dynamic folder mode**. In this mode:

* the `asset_folder` controls where the asset appears in the Cloudinary interface;
* the `public_id` controls the delivery-URL path;
* moving or renaming an asset folder does not automatically change the delivery URL.

Legacy environments may use **fixed folder mode**, where the folder path is part of the public ID and therefore influences the delivery URL.

The CLI handles the source directory hierarchy automatically. Custom Python scripts must deliberately choose the appropriate parameters for the product environment.

<h1 align="center"><i>Validation Strategy</i></h1>

A migration should not be considered complete merely because the upload command has finished.

Validation should include:

1. counting eligible source files;
2. counting prepared staging files;
3. reviewing the CLI or Python exit status;
4. recording successful and failed uploads;
5. confirming that the expected Cloudinary folders exist;
6. opening a sample of assets from different folders;
7. checking filenames, public IDs, formats, and delivery URLs;
8. comparing the number of successful manifest rows with the source count;
9. reprocessing only failed items where necessary;
10. disabling temporary migration credentials after sign-off.

<h1 align="center"><i>Skills Demonstrated</i></h1>

* Designing an ETL process for digital media.
* Extracting assets from Git repositories and local filesystems.
* Recursively discovering files with Python and PowerShell.
* Filtering media with extension allowlists.
* Preserving relative directory hierarchies.
* Creating staging areas for controlled migration.
* Installing and configuring the Cloudinary CLI.
* Managing secrets through temporary environment variables.
* Uploading complete folder structures programmatically.
* Supporting dynamic and legacy fixed folder modes.
* Creating migration manifests and operational logs.
* Applying retry logic and exception handling.
* Validating source and destination asset counts.
* Cleaning up temporary data and credentials.
* Documenting a reproducible technical workflow.

<h1 align="center"><i>Technologies Used</i></h1>

<table align="center">
<tr>
<td>
<i>

* Cloudinary
* Cloudinary CLI
* Cloudinary Python SDK
* Python
* PowerShell
* Git
* GitHub
* CSV manifests
* Virtual environments
* Environment variables
* ETL methodology

</i>
</td>
</tr>
</table>

<h1 align="center"><i>Overall Summary</i></h1>

This project provides a practical and reusable framework for migrating media assets from a Git repository, local folder, synchronised drive, exported storage location, or other filesystem-accessible source into Cloudinary.

The migration is organised around an ETL and validation workflow. Assets are extracted from the source, transformed into a controlled and filtered staging structure, loaded into Cloudinary, and validated through source counts, upload results, manifests, and visual inspection.

The Cloudinary CLI offers the fastest route for a complete directory migration, while the Python ETL example provides greater control over file selection, folder mapping, retries, metadata, public IDs, logging, and auditability. Together, these approaches form a strong foundation for one-time migrations as well as future automated media-ingestion pipelines.

<h1 align="center"><i>References</i></h1>

* [Cloudinary Command Line Interface](https://cloudinary.com/documentation/cloudinary_cli)
* [Cloudinary Migration Guide](https://cloudinary.com/documentation/migration)
* [Cloudinary Folder Modes](https://cloudinary.com/documentation/folder_modes)
* [Cloudinary Python SDK Quick Start](https://cloudinary.com/documentation/python_quickstart)
* [Cloudinary Upload API Reference](https://cloudinary.com/documentation/image_upload_api_reference)
* [GitHub: Cloning a Repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
* [Python Virtual Environments](https://docs.python.org/3/library/venv.html)

# Author
# ***[Matteo Meloni](https://www.linkedin.com/in/matteo-meloni-40a357154/)***
