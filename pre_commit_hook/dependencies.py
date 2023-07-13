import logging
from pre_commit_hook.errors import CheckDependenciesError
from pre_commit_hook.utils import exec_sync_command

logger = logging.getLogger("check-dependencies")


def check_dependencies() -> str:
    """
    Check dependencies versions
    """
    try:
        return exec_sync_command(('go', 'list', '-m', '-f',
                      '\'{{if and (not (or .Indirect .Main)) .Update}}{{.Path}}: {{.Version}} -----> {{.Update.Version}}{{end}}\'',
                      '-u', 'all'))
    except Exception as e:
        logger.error("there was an error checking dependencies versions. [error:%s]", e)
        raise CheckDependenciesError(e)