import os
import logging
from pre_commit_hook.git import get_git_directory

logger = logging.getLogger("tmp-file")

def get_tmp_path() -> str:
    git_directory = get_git_directory()
    tmp_file = ".pre-commit-hook-tmp"
    return f"{git_directory}/{tmp_file}"

def save_on_tmp(uuid, version, exit_code):
    """
    Create a temporal file and write down the uuid and the exit_code
    :param uuid The hook's execution id
    :param exit_code The hook's executions exit_code
    """
    try:
        tmp_path = get_tmp_path()
        file = open(tmp_path, 'w')
        file.write(f"{uuid},{version},{exit_code}")
        file.close()
    except Exception as e:
        logger.error("there was an error writing temporal file. [uuid:%s][exit_code:%s][error:%s]", uuid, exit_code, e)

def clean_after():
    """
    Removes the temporal file.
    """
    try:
        tmp_path = get_tmp_path()
        os.remove(tmp_path)
    except Exception as e:
        logger.error("there was an error removing temporal file. [error:%s]",e)

def get_tmp_file_content():
    """
    Returns the temporal file content
    """
    content = ""
    try:
        tmp_path = get_tmp_path()
        file = open(tmp_path, 'r')
        content = file.read()
        file.close()
    except Exception as e:
        logger.error("there was an error getting tmp file content. [error:%s]",e)
    finally:
        return content

def get_uuid(content):
    """
    Returns the uuid from the temporal file content
    :param content The temporal file content
    """
    return content.split(",")[0]

def get_exit_code(content) -> int :
    """
    Returns the exit_code from the temporal file content
    :param content The temporal file content
    """
    cnt = content.split(",")
    if len(cnt) < 2:
        return -1
    return int(cnt[1])