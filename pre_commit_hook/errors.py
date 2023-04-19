class UnexpectedError(Exception):
    """
    Unexpected exception raised.
    :param message Explanation of the error
    """

    def __init__(self, message: str):
        super().__init__(message)


class RepoError(Exception):
    """
    Invalid repository.
    :param message Explanation of the error
    """

    def __init__(self, ex: Exception):
        super().__init__(f"Repository not found: {ex}")


class UserError(Exception):
    """
    Invalid user.
    :param message Explanation of the error
    """

    def __init__(self):
        super().__init__("No user found")


class GitDirectoryError(Exception):
    """
    An exception was raised when trying to get git directory
    :param message Explanation of the error
    """

    def __init__(self, ex: Exception):
        super().__init__(f"error getting git directory: {ex}")


class CheckDependenciesError(Exception):
    """
    An exception was raised when trying to checking dependencies versions
    :param message Explanation of the error
    """

    def __init__(self, ex: Exception):
        super().__init__(f"Error checking dependencies versions: {ex}")
