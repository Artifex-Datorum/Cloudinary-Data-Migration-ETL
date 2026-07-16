<h1 align="center">Cloudinary Data Migration Resolution Case Study</h1>

<h1 align="center">Exercise 1: Understand the migration objective</h1>

The objective of this project is to migrate a hierarchy of digital media assets into Cloudinary while preserving the logical folder structure and maintaining a clear audit trail.

The source does not need to be GitHub. It can be any location that can be made available as a local directory, including:

| Source type | Extraction method |
| --- | --- |
| GitHub, GitLab, or another Git host | Clone the repository with Git. |
| Local computer folder | Use the existing directory directly. |
| Google Drive, OneDrive, or Dropbox | Synchronise the folder locally first. |
| Network or shared drive | Mount or copy the required folder. |
| Object-storage export | Download or mount the exported directory. |
| List of remote URLs | Use a specialised migration script or Cloudinary migration command. |
| External DAM export | Extract the archive and prepare its media directory. |

The migration follows five controlled phases:

```text
Extract → Transform → Load → Validate → Close
```

| Phase | Purpose |
| --- | --- |
| `Extract` | Obtain the source assets in a local filesystem-accessible location. |
| `Transform` | Filter files, preserve relative paths, remove irrelevant content, and prepare staging data. |
| `Load` | Upload the prepared assets into Cloudinary. |
| `Validate` | Compare counts, inspect folder structure, review failures, and open sample assets. |
| `Close` | Remove credentials, staging data, temporary keys, and test assets. |

<h1 align="center">Exercise 2: Plan the destination structure</h1>

Before uploading any files, determine the intended root folder in Cloudinary.

For example:

```text
Migrated-Assets
├── Brand
├── Certifications
├── Dashboards
├── Documentation
├── Product Images
└── Screenshots
```

The source hierarchy beneath the selected source directory should be treated as relative. If the source is:

```text
C:\Migration\Source-Assets\Product Images\Catalogue\item-001.png
```

and the Cloudinary destination is:

```text
Migrated-Assets
```

the intended Cloudinary asset-folder location becomes:

```text
Migrated-Assets/Product Images/Catalogue
```

The source directory itself can either be included or excluded from the final hierarchy. In this project, `--exclude-dir-name` is used so that a temporary staging-folder name is not duplicated inside Cloudinary.

<h1 align="center">Exercise 3: Extract the assets</h1>

## Option A: Clone a Git repository

Open PowerShell, select a working directory, and clone the repository.

```powershell
cd "$env:USERPROFILE\Downloads"

git clone https://github.com/USERNAME/REPOSITORY.git
```

Confirm the result:

```powershell
Test-Path "$env:USERPROFILE\Downloads\REPOSITORY"
```

The expected result is:

```text
True
```

## Option B: Use a local folder

Set the source path directly:

```powershell
$source = "C:\Path\To\Source-Assets"
```

Confirm that it exists:

```powershell
Test-Path $source
```

## Option C: Use a synchronised cloud folder

Synchronise the required Google Drive, OneDrive, or Dropbox folder to the local computer, then set the synchronised directory as the source:

```powershell
$source = "$env:USERPROFILE\OneDrive\Media-Archive"
```

The remaining process is identical because the migration operates on the local filesystem representation.

<h1 align="center">Exercise 4: Inspect and profile the source</h1>

Before transforming or uploading the data, inspect the source directory.

Count all files:

```powershell
$allFiles = Get-ChildItem `
    -Path $source `
    -Recurse `
    -File

Write-Host "All files:" $allFiles.Count
```

Count selected media types:

```powershell
$allowedExtensions = @(
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".mp4",
    ".mov",
    ".pdf"
)

$eligibleFiles = Get-ChildItem `
    -Path $source `
    -Recurse `
    -File |
Where-Object {
    $_.Extension.ToLower() -in $allowedExtensions
}

Write-Host "Eligible media files:" $eligibleFiles.Count
```

Display the ten largest eligible files:

```powershell
$eligibleFiles |
    Sort-Object Length -Descending |
    Select-Object `
        -First 10 `
        FullName,
        @{Name="SizeMB"; Expression={
            [math]::Round($_.Length / 1MB, 2)
        }}
```

This profiling stage helps identify:

* unexpected file types;
* unusually large assets;
* duplicate names;
* hidden source-control content;
* files that may exceed plan or upload restrictions;
* folders that contain no eligible media.

<h1 align="center">Exercise 5: Install Python and create a virtual environment</h1>

Check whether Python is available:

```powershell
py --version
```

or:

```powershell
python --version
```

Create an isolated environment:

```powershell
$venv = "$env:USERPROFILE\CloudinaryMigrationEnv"

py -m venv $venv
```

Activate it:

```powershell
& "$venv\Scripts\Activate.ps1"
```

The PowerShell prompt should now begin with:

```text
(CloudinaryMigrationEnv)
```

Upgrade `pip`:

```powershell
python -m pip install --upgrade pip
```

A virtual environment isolates the migration dependencies from the computer's global Python installation.

<h1 align="center">Exercise 6: Install the Cloudinary CLI</h1>

Install the command-line interface:

```powershell
python -m pip install cloudinary-cli
```

Verify it:

```powershell
cld --version
```

The output should identify:

* the Cloudinary CLI version;
* the Cloudinary SDK version;
* the Python version.

The Cloudinary CLI includes `upload_dir`, which is the principal command used in this migration because it uploads a complete directory while maintaining the source hierarchy.

<h1 align="center">Exercise 7: Create a dedicated migration API key</h1>

Open the Cloudinary Console and navigate to:

```text
Settings → API Keys
```

Generate a new key named, for example:

```text
Repository migration
```

A temporary or dedicated key is preferable because it can be disabled immediately after the migration.

Obtain:

* the cloud name;
* the API key;
* the API secret.

The Cloudinary environment-variable format is:

```text
cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Never place the real value in:

* Git;
* a README;
* source code;
* `.env.example`;
* screenshots;
* issue descriptions;
* migration logs.

<h1 align="center">Exercise 8: Configure the credentials securely</h1>

Use a secure PowerShell prompt:

```powershell
$secureCloudinaryUrl = Read-Host `
    "Paste the complete Cloudinary URL" `
    -AsSecureString
```

Paste the complete value and press `Enter`. Nothing will be displayed while pasting.

Create the temporary environment variable:

```powershell
$env:CLOUDINARY_URL = [System.Net.NetworkCredential]::new(
    "",
    $secureCloudinaryUrl
).Password
```

Remove the temporary input variable:

```powershell
Remove-Variable secureCloudinaryUrl
```

Verify the target environment:

```powershell
cld config
```

Check that the displayed `cloud_name` matches the intended Cloudinary product environment before uploading anything.

<h1 align="center">Exercise 9: Conduct a one-file test</h1>

A test upload should always precede the complete migration.

Create a clean temporary directory:

```powershell
$testSource = Join-Path `
    $env:TEMP `
    "cloudinary-migration-test"

Remove-Item `
    -Path $testSource `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

New-Item `
    -ItemType Directory `
    -Path $testSource |
    Out-Null
```

Select and copy one eligible asset:

```powershell
$firstAsset = $eligibleFiles |
    Select-Object -First 1

Copy-Item `
    -Path $firstAsset.FullName `
    -Destination $testSource
```

Confirm that the folder contains exactly one file:

```powershell
Get-ChildItem $testSource
```

Upload the test:

```powershell
cld upload_dir `
    --folder "_migration_test" `
    --exclude-dir-name `
    --concurrent_workers 1 `
    "$testSource"
```

In Cloudinary, open:

```text
Assets → Folders → _migration_test
```

Confirm that:

* the asset exists;
* the thumbnail is visible;
* the complete asset opens correctly;
* the expected format is shown;
* the upload used the intended Cloudinary environment.

Do not proceed until the test is successful.

<h1 align="center">Exercise 10: Transform the source into a staging directory</h1>

The staging directory should contain only the files intended for migration.

Set the paths:

```powershell
$staging = "$env:USERPROFILE\Downloads\Cloudinary-Migration-Staging"
```

Remove an older staging directory if present:

```powershell
Remove-Item `
    -Path $staging `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue
```

Create a new one:

```powershell
New-Item `
    -ItemType Directory `
    -Path $staging |
    Out-Null
```

## PNG-only example

```powershell
robocopy `
    "$source" `
    "$staging" `
    "*.png" `
    /S `
    /R:1 `
    /W:1
```

## Multiple-extension example

Run one `robocopy` command for each extension:

```powershell
$patterns = @(
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.webp",
    "*.gif",
    "*.svg",
    "*.mp4",
    "*.mov",
    "*.pdf"
)

foreach ($pattern in $patterns) {
    robocopy `
        "$source" `
        "$staging" `
        "$pattern" `
        /S `
        /R:1 `
        /W:1
}
```

The `/S` option copies populated subdirectories and therefore preserves the relative hierarchy.

Robocopy uses special exit-code semantics. Codes below `8` generally indicate that no fatal copy failure occurred, while `8` or higher indicates at least one failed copy operation.

Store the result of each invocation if strict automation is required.

<h1 align="center">Exercise 11: Validate the staging directory</h1>

Count eligible source assets:

```powershell
$sourceCount = (
    Get-ChildItem `
        -Path $source `
        -Recurse `
        -File |
    Where-Object {
        $_.Extension.ToLower() -in $allowedExtensions
    }
).Count
```

Count staging assets:

```powershell
$stagingCount = (
    Get-ChildItem `
        -Path $staging `
        -Recurse `
        -File
).Count
```

Compare the results:

```powershell
Write-Host "Eligible source files:" $sourceCount
Write-Host "Staging files:" $stagingCount

if ($sourceCount -ne $stagingCount) {
    throw "The source and staging counts do not match."
}

Write-Host "The staging directory is complete."
```

Do not begin the complete upload if the counts differ.

Possible causes of a mismatch include:

* an omitted extension;
* a case-sensitive filtering mistake in another shell;
* duplicate copy commands;
* inaccessible source files;
* a previously populated staging folder;
* files changing while the staging operation is running.

<h1 align="center">Exercise 12: Upload the complete folder structure</h1>

Run:

```powershell
cld upload_dir `
    --folder "Migrated-Assets" `
    --exclude-dir-name `
    --concurrent_workers 8 `
    "$staging"
```

The options perform the following functions:

| Option | Purpose |
| --- | --- |
| `--folder` | Selects the root Cloudinary destination. |
| `--exclude-dir-name` | Excludes the local staging directory's own name from the destination hierarchy. |
| `--concurrent_workers 8` | Processes several uploads concurrently. |
| `"$staging"` | Identifies the prepared local directory to upload. |

Keep the terminal open until the command has completed.

<h1 align="center">Exercise 13: Check the command result</h1>

Immediately save the exit code:

```powershell
$uploadExitCode = $LASTEXITCODE
```

Display it:

```powershell
Write-Host `
    "Cloudinary upload exit code:" `
    $uploadExitCode
```

A successful command normally returns:

```text
0
```

The exit code is useful but is not sufficient by itself. Destination validation must still be performed.

<h1 align="center">Exercise 14: Validate Cloudinary</h1>

Open:

```text
Cloudinary → Assets → Folders → Migrated-Assets
```

Validate the migration systematically.

## Folder validation

Confirm that:

* all expected top-level folders exist;
* nested subfolders are present;
* no temporary staging-folder name has been duplicated;
* no test folder has been mixed into production assets.

## Asset validation

Open a sample from:

* the root folder;
* several first-level folders;
* at least one deeply nested folder;
* each major media format;
* the largest-file group.

Confirm:

* correct rendering;
* correct display name;
* expected dimensions or duration;
* appropriate Cloudinary resource type;
* working secure delivery URL.

## Count validation

Compare:

```text
Eligible source count
        =
Staging count
        =
Successful destination uploads
```

For a Python ETL, use the manifest's `success` rows as the destination count.

<h1 align="center">Exercise 15: Understand Cloudinary folder modes</h1>

Cloudinary environments use either dynamic or legacy fixed folders.

## Dynamic folder mode

In dynamic folder mode:

* `asset_folder` controls the location shown in the Cloudinary interface;
* `display_name` controls the user-facing asset name;
* `public_id` controls the delivery URL;
* moving an asset to another folder does not automatically change its public ID or delivery URL.

The CLI automatically recreates the local folder structure as asset folders.

## Fixed folder mode

In fixed folder mode:

* the folder forms part of the public ID;
* moving or renaming content can affect delivery URLs;
* Python code normally uses the legacy `folder` parameter.

For a custom ETL, confirm the product environment's folder mode before selecting upload parameters.

<h1 align="center">Exercise 16: Implement a reusable Python ETL</h1>

For advanced migrations, create:

```text
scripts/migrate_assets.py
```

Use the complete Python implementation contained in the repository README. The script performs:

1. argument parsing;
2. credential validation;
3. recursive asset discovery;
4. extension filtering;
5. relative-path preservation;
6. dynamic or fixed folder configuration;
7. retry handling;
8. Cloudinary uploading;
9. CSV manifest creation;
10. exit-code reporting.

Install the Python SDK:

```powershell
python -m pip install cloudinary
```

Run the ETL:

```powershell
python scripts\migrate_assets.py `
    --source "C:\Path\To\Source-Assets" `
    --destination "Migrated-Assets" `
    --folder-mode dynamic `
    --manifest "manifests\migration_manifest.csv"
```

Example output:

```text
Discovered assets: 147
Successful uploads: 147
Failed uploads: 0
Manifest: C:\Project\manifests\migration_manifest.csv
```

<h1 align="center">Exercise 17: Review the migration manifest</h1>

The Python ETL writes these fields:

| Field | Meaning |
| --- | --- |
| `source_file` | Absolute source path. |
| `relative_path` | Source path relative to the migration root. |
| `status` | `success` or `failed`. |
| `asset_id` | Immutable Cloudinary asset identifier. |
| `public_id` | Identifier used in Cloudinary delivery URLs. |
| `asset_folder` | Cloudinary interface folder or legacy folder value. |
| `resource_type` | Image, video, or raw resource classification. |
| `format` | Detected asset format. |
| `secure_url` | HTTPS delivery URL returned by Cloudinary. |
| `error` | Exception message for failed uploads. |

Use PowerShell to inspect failed rows:

```powershell
Import-Csv `
    "manifests\migration_manifest.csv" |
Where-Object {
    $_.status -eq "failed"
} |
Format-Table `
    relative_path,
    error `
    -AutoSize
```

If no rows are returned, the manifest contains no failed uploads.

<h1 align="center">Exercise 18: Reprocess failures safely</h1>

Do not repeat the complete migration blindly when only a few files fail.

Instead:

1. identify failed manifest rows;
2. determine whether the cause is connectivity, filename handling, credentials, format, size, or access;
3. place only failed source files into a retry staging directory;
4. conduct a new one-file test when configuration changes;
5. upload the retry staging directory;
6. append or merge the new results into the audit record.

This limits duplicate work and reduces the risk of overwriting valid assets.

<h1 align="center">Exercise 19: Remove the test data</h1>

After the complete migration has been validated:

1. open `_migration_test` in Cloudinary;
2. delete the test asset;
3. delete the empty test folder.

Remove the local test directory:

```powershell
Remove-Item `
    -Path $testSource `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue
```

<h1 align="center">Exercise 20: Close the Cloudinary connection</h1>

Remove the temporary environment variable:

```powershell
Remove-Item Env:CLOUDINARY_URL `
    -ErrorAction SilentlyContinue
```

Remove any credential variables:

```powershell
Remove-Variable `
    cloudName,
    apiKey,
    apiSecret,
    apiSecretSecure,
    secureCloudinaryUrl `
    -ErrorAction SilentlyContinue
```

Confirm that the Cloudinary URL is no longer present:

```powershell
$env:CLOUDINARY_URL
```

The expected output is empty.

<h1 align="center">Exercise 21: Remove staging data</h1>

After sign-off:

```powershell
Remove-Item `
    -Path $staging `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue
```

Do not remove the original source directory unless the organisation's retention policy permits it.

Leave the virtual environment:

```powershell
deactivate
```

Optionally remove the migration environment:

```powershell
Remove-Item `
    "$env:USERPROFILE\CloudinaryMigrationEnv" `
    -Recurse `
    -Force
```

<h1 align="center">Exercise 22: Disable the migration API key</h1>

Return to:

```text
Cloudinary → Settings → API Keys
```

Locate the dedicated migration key and disable it after the migration has been validated.

If any credential was accidentally exposed:

1. generate a replacement key;
2. test the replacement;
3. disable the exposed key;
4. remove it from shell history, logs, screenshots, and files;
5. review the Cloudinary audit information where available.

<h1 align="center">Exercise 23: Clear sensitive PowerShell history</h1>

When a secret has accidentally been entered directly into a command, clear the current session:

```powershell
Clear-History
```

To remove the saved PSReadLine history for the current Windows user:

```powershell
$historyPath = (
    Get-PSReadLineOption
).HistorySavePath

Remove-Item `
    -Path $historyPath `
    -Force `
    -ErrorAction SilentlyContinue
```

This removes the complete saved PowerShell command history, not only the Cloudinary commands.

The exposed API key must still be rotated or disabled because deleting local history does not make an exposed credential safe again.

<h1 align="center">Exercise 24: Troubleshooting</h1>

## `git` is not recognised

Git is not installed or is not available through `PATH`.

Use a downloaded ZIP archive, GitHub Desktop, or install Git according to organisational policy.

## `python` is not recognised but `py` works

Use:

```powershell
py --version
py -m pip --version
```

Create the environment with:

```powershell
py -m venv "$env:USERPROFILE\CloudinaryMigrationEnv"
```

## PowerShell execution-policy warning

Check whether activation succeeded. If the prompt contains the virtual-environment name, continue. On managed computers, policy may be controlled by the organisation.

Do not bypass corporate security controls without authorisation.

## `cld` is not recognised

Activate the correct virtual environment and reinstall:

```powershell
& "$env:USERPROFILE\CloudinaryMigrationEnv\Scripts\Activate.ps1"

python -m pip install cloudinary-cli
```

## `cld config` shows the wrong cloud name

Remove the malformed environment variable:

```powershell
Remove-Item Env:CLOUDINARY_URL `
    -ErrorAction SilentlyContinue
```

Then re-enter the complete Cloudinary URL securely.

## `Got unexpected extra arguments`

This can happen when PowerShell expands an unquoted wildcard into many filenames.

Avoid the wildcard by preparing a staging folder containing only the required files:

```powershell
cld upload_dir `
    --folder "Migrated-Assets" `
    --exclude-dir-name `
    "$staging"
```

## Duplicate filenames in different folders

Dynamic folder mode separates asset-folder placement from the public ID. Confirm the upload-preset naming behaviour before using deterministic filename-based IDs.

The Python ETL avoids accidental cross-folder collisions by assigning a public ID based on the complete relative path in dynamic mode.

## Folder structure appears correct but URLs differ

In dynamic folder mode, the folder shown in Cloudinary and the public-ID delivery path are separate properties. This is expected.

## The command succeeds but some assets are missing

Compare the source count, staging count, CLI output, Cloudinary destination, and Python manifest. Check unsupported formats, permissions, size restrictions, and failed requests.

<h1 align="center">Exercise 25: Final checklist</h1>

| Requirement | Completed? |
| --- | --- |
| The source directory has been obtained and confirmed. | ☐ |
| Eligible file types have been defined. | ☐ |
| The source file count has been recorded. | ☐ |
| A virtual environment has been created. | ☐ |
| The Cloudinary CLI or Python SDK has been installed. | ☐ |
| A dedicated migration API key has been created. | ☐ |
| `cld config` shows the correct cloud name. | ☐ |
| A one-file test upload has succeeded. | ☐ |
| A filtered staging directory has been prepared. | ☐ |
| The source and staging counts match. | ☐ |
| The complete directory has been uploaded. | ☐ |
| The Cloudinary folder hierarchy has been inspected. | ☐ |
| Sample assets have been opened successfully. | ☐ |
| Failed uploads have been reviewed or reprocessed. | ☐ |
| The migration manifest has been retained where required. | ☐ |
| The test asset and test folder have been removed. | ☐ |
| `CLOUDINARY_URL` has been removed. | ☐ |
| The migration API key has been disabled. | ☐ |
| Temporary staging data has been removed. | ☐ |
| Exposed credentials, if any, have been rotated. | ☐ |

<h1 align="center">Exercise 26: Overall resolution</h1>

The migration is complete when:

```text
Eligible source assets
        =
Prepared staging assets
        =
Successfully migrated Cloudinary assets
```

and when the following conditions are true:

* the destination folder hierarchy is correct;
* representative assets open successfully;
* no unresolved failures remain;
* temporary credentials have been removed;
* the migration key has been disabled;
* the audit manifest and required logs have been retained;
* temporary staging and test data have been deleted.

This workflow can be reused for future migrations from Git repositories, local archives, shared drives, synchronised cloud directories, and other filesystem-accessible media sources.

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
