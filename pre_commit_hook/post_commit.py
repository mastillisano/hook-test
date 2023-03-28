from __future__ import annotations
import logging
from pre_commit_hook.git import get_user, get_commit, get_repository
from pre_commit_hook.utils import is_check_skipped
from pre_commit_hook.tmp_file import get_tmp_file_content, get_exit_code, get_uuid, clean_after
from pre_commit_hook.configs import precommit_url, version
from pre_commit_hook.requests import make_request
from pre_commit_hook.errors import ClientError

def main() -> int:
    """
    Notifies sast-precommit API of uuid, commit and exit_code
    """
    uuid = None
    commit = None
    exit_code = None
    try:
        content = get_tmp_file_content()
        uuid = get_uuid(content)
        commit = get_commit()
        exit_code = get_exit_code(content)
        notify(uuid,commit, exit_code)
    except Exception as e:
        logger = logging.getLogger("post-commit")
        logger.error("[uuid:%s][commit:%s][exit_code:%s][error:%s]",
                uuid, commit, exit_code, e)
    finally:
        clean_after()
        return 0

def notify(uuid, commit, exit_code):
    """
    Returns the repository name (owner/name)
    :param uuid The hook execution id
    :param commit The commit just created
    :param exit_code The exit_code of the pre-commit hook 
    (this is the actual exit code, if the check was skipped the hook always returns 0, but this refers to the actual exit code)
    """
    response = {}
    payload = {"commit":commit,"exit_code":exit_code, "version": version}
    res = make_request("PUT",f"{precommit_url}/{uuid}", payload)

if __name__ == '__main__':
    raise SystemExit(main())