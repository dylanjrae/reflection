import logging as log
from dotenv import dotenv_values
import os
from merge.client import Merge
from merge.core.api_error import ApiError
from merge.resources.filestorage.types import PaginatedFileList
from merge.resources.filestorage.types.folder_request import FolderRequest
from merge.resources.filestorage.types.folder import Folder
from merge.resources.filestorage.types.file import File
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


def get_all_files_in_backup_folder(merge_client: Merge, folder_id: str) -> list[File]:
    all_files = []
    try:
        # Get all files in the current folder
        files: list[File] = merge_client.filestorage.files.list(
            folder_id=folder_id
        ).results
        all_files.extend(files)

        # Get all subfolders in the current folder
        folders: list[Folder] = merge_client.filestorage.folders.list(
            parent_folder_id=folder_id
        ).results

        # Recursively fetch files in each subfolder
        for folder in folders:
            all_files.extend(get_all_files_in_backup_folder(merge_client, folder.id))
    except ApiError as e:
        log.error(e.body)

    return all_files


def get_all_local_files(dirs: list[str]) -> list[str]:
    all_files = []
    for dir in dirs:
        for root, dirs, files in os.walk(dir):
            for file in files:
                all_files.append(os.path.join(root, file))
    return all_files


def find_missing_files(merge_files: list[File], local_files: list[str]) -> list[str]:
    missing_files = []
    for local_file in local_files:
        if not any(merge_file.name == local_file for merge_file in merge_files):
            missing_files.append(local_file)
    return missing_files


def upload_files(merge_client: Merge, folder_id: str, files: list[str]):
    for file in files:
        try:
            # TODO need to add a file_url to upload from --> maybe a future project is a secure locally hosted python file url system?
            file_create_result: FileStorageFileResponse = (
                merge_client.filestorage.files.create(
                    model=File(name=file, folder_id=folder_id)
                )
            )
        except ApiError as e:
            log.error(e.body)
        log.debug(f"Uploaded {file}!")


def upload_all_missing_files(merge_client: Merge, dirs: list[str]):
    # get current files in backup folder
    # get folder id
    backup_folder: Folder = merge_client.filestorage.folders.list(
        name="reflection-backup"
    ).results[0]
    merge_files = get_all_files_in_backup_folder(merge_client, backup_folder.id)
    local_files = get_all_local_files(dirs)
    files_to_upload = find_missing_files(merge_files, local_files)
    upload_files(merge_client, backup_folder.id, files_to_upload)


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
    upload_all_missing_files(drive_merge_client, dirs)

    # files: PaginatedFileList = merge_client.filestorage.files.list()
    # log.debug(files.json())
    # log.debug(vars(files))


if __name__ == "__main__":
    main()
