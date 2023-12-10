import logging as log
from dotenv import dotenv_values
import os
from merge.client import Merge
from merge.core.api_error import ApiError
from merge.resources.filestorage.types import PaginatedFileList
from merge.resources.filestorage.types.folder_request import FolderRequest
from merge.resources.filestorage.types.folder import Folder
from merge.resources.filestorage.types.file_storage_file_response import (
    FileStorageFileResponse,
)


def load_dirs() -> list[str]:
    return ["/Users/dylan/Documents/relfection-backup"]


def verify_local_dirs_exist(dir: str):
    if not os.path.exists(dir):
        log.error(f"Directory {dir} does not exist!")
        exit(1)


def create_drive_merge_client() -> Merge:
    env_vars = dotenv_values(".env")
    merge_client = Merge(
        api_key=env_vars["API_KEY"], account_token=env_vars["DRIVE_ACCOUNT_TOKEN"]
    )
    log.getLogger("httpx").setLevel(log.WARNING)
    log.getLogger("httpcore.http11").setLevel(log.WARNING)
    log.getLogger("httpcore.connection").setLevel(log.WARNING)
    return merge_client


def verify_account_link(merge_client: Merge):
    try:
        linked_accounts = merge_client.filestorage.linked_accounts.list()
    except ApiError as e:
        log.error(e.body)


def create_backup_folder_if_not_exists(merge_client: Merge):
    try:
        folder_list: list[Folder] = merge_client.filestorage.folders.list(
            name="reflection-backup"
        ).results
    except ApiError as e:
        log.error(e.body)
        log.error("Failed to get list of folders!")
        exit(1)

    if not any(folder.name == "reflection-backup" for folder in folder_list):
        try:
            folder_create_result: FileStorageFileResponse = (
                merge_client.filestorage.folders.create(
                    model=FolderRequest(name="reflection-backup")
                )
            )
        except ApiError as e:
            log.error(e.body)
        log.debug("Created backup folder!")
    else:
        log.debug("Backup folder already exists!")


def main():
    log.basicConfig(level=log.DEBUG, format="%(message)s")

    log.debug("Hello, welcome to reflection!")
    dirs: list[str] = load_dirs()
    log.debug(
        "Reflection is currently configured to backup the following directories:\n"
    )
    for dir in dirs:
        log.debug(dir)
        verify_local_dirs_exist(dir)

    log.debug("\nReflection will now begin backing up your files...")
    drive_merge_client = create_drive_merge_client()
    verify_account_link(drive_merge_client)
    create_backup_folder_if_not_exists(drive_merge_client)

    # files: PaginatedFileList = merge_client.filestorage.files.list()
    # log.debug(files.json())
    # log.debug(vars(files))


if __name__ == "__main__":
    main()
