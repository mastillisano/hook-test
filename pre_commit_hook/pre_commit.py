import logging
import traceback
from pre_commit_hook.errors import UserError, RepoError, CheckDependenciesError
from pre_commit_hook.utils import generate_uuid, exec_command
from pre_commit_hook.git import get_repository, get_user
from pre_commit_hook.tmp_file import save_on_tmp
from pre_commit_hook.configs import version
from pre_commit_hook.colors import red, soft_white, reset

logger = logging.getLogger("pre-commit")


def main():
    """
    Analyze dependency versions and report if there are new versions
    When check skipped is True, this always returns 0.
    """
    exit_code = 0
    check_skipped = False
    uuid = None
    repo = None
    result = ""
    try:
        uuid = generate_uuid()
        email = get_user()
        repo = get_repository()
        result = check_dependencies()
        if result == "":
            print(f"{soft_white}*** These dependencies must be updated ***\n\n{result}{reset}")
    except UserError as err:
        exit_code = 1
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]", repo, check_skipped, exit_code, uuid, err)
        print(f"{red}No user was found. Please set up your user email with `git config user.email ...` or with --global to set it globally.{reset}")
    except RepoError as err:
        exit_code = 2
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]", repo, check_skipped, exit_code, uuid, err)
        print(f"{red}No repository was found. Please set up your repository url with `git config remote.origin.url <repo url>`.{reset}")
    except CheckDependenciesError as err:
        exit_code = 3
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]", repo, check_skipped, exit_code, uuid, err)
        print(f"{red}There was an error checking dependencies versions.{reset}")
    except Exception as err:
        exit_code = 4
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:[msg:%s][type:%s][stack_trace:%s]]", repo, check_skipped, exit_code, 
                     uuid, err, type(err).__name__, traceback.format_exc())
        print(f"{red}There was an unexpected error processing your commit.\nPlease contact us in slack channel #ops-it-team.{reset}")
    finally:
        # if skip_check is TRUE or exit_code is 0, then the commit is NOT blocked, only on that case the file is created
        if exit_code == 0 or check_skipped:
            save_on_tmp(uuid, version, exit_code)
        if check_skipped:
            return 0
        return exit_code


def check_dependencies() -> str:
    """
    Check dependencies versions
    """
    try:
        return exec_command(('go', 'list', '-m', '-u', 'all'))
    except Exception as e:
        logger.error("there was an error checking dependencies versions. [error:%s]", e)
        raise CheckDependenciesError(e)


if __name__ == '__main__':
    raise SystemExit(main())
