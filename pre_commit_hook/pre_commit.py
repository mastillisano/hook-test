import string
import logging
import traceback
from pre_commit_hook.errors import RequestError, DiffError, UserError, RepoError
from pre_commit_hook.utils import generate_uuid, is_check_skipped
from pre_commit_hook.git import get_repository, get_user, get_diff
from pre_commit_hook.tmp_file import save_on_tmp
from pre_commit_hook.requests import make_request
from pre_commit_hook.configs import precommit_url, version
from pre_commit_hook.colors import red, cyan, bold, soft_white, reset

MAX_SIZE = 100000 # 100KB
CONST_PAGE_SIZE = 9
logger = logging.getLogger("pre-commit")

def main():
    """
    Analyzes the changes introduced, if credentials are detected, the commit is not created.
    When check skipped is True, this always returns 0.
    """
    exit_code = 0
    check_skipped = False
    uuid = None
    repo = None
    try:
        check_skipped = is_check_skipped()
        uuid = generate_uuid()
        repo = get_repository()
        email = get_user()
        diff = get_diff()
        files = processDiff(diff)
        exit_code = processFiles(uuid, repo, email, check_skipped, files)
    except RequestError as err:
        exit_code = 2
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:[msg:%s][status_code:%s][url:%s][reponse_text:%s]]",
                repo, check_skipped, exit_code, uuid, err, err.status_code, err.url, err.response_text)
        print(f"{red}{err.client_msg}{reset}")
    except DiffError as err:
        exit_code = 3
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]",
                repo, check_skipped, exit_code, uuid, err)
        print(f"{red}There was an error getting the diff. Try again and create a ticket on Fury Support Precommit > Websec Hook > Fails if the error persists.{reset}")
    except UserError as err:
        exit_code = 6
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]",
                repo, check_skipped, exit_code, uuid, err)
        print(f"{red}No user was found. Please set up your user email with `git config user.email ...` or with --global to set it globally.{reset}")
    except RepoError as err:
        exit_code = 7
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:%s]",
                repo, check_skipped, exit_code, uuid, err)
        print(f"{red}No repository was found. Please set up your repository url with `git config remote.origin.url <repo url>`.{reset}")
    except Exception as err:
        exit_code = 4
        logger.error("[repo:%s][check_skipped:%s][exit_code:%s][uuid:%s][error:[msg:%s][type:%s][stack_trace:%s]]",
                repo, check_skipped, exit_code, uuid, err, type(err).__name__, traceback.format_exc())
        print(f"{red}There was an unexpected error processing your commit.\nCheck the FAQ section of the official docs first, maybe this issue is solved there: https://furydocs.io/sast-precommit//guide/#/lang-en/FAQs.\nIf not, please create a ticket on Fury Support Precommit > Websec Hook > Fails.{reset}")
    finally:
        ## if skip_check is TRUE or exit_code is 0, then the commit is NOT blocked, only on that case the file is created
        if exit_code == 0 or check_skipped:
            save_on_tmp(uuid, exit_code)
        if check_skipped:
            return 0
        return exit_code

def processDiff(diff): # the type was removed because of a problem with python < 3.9
    """
    Returns the additions by file
    :param diff The diff of changes
    """
    lines = diff.split("\n")
    file_name = ""
    files = {}
    for line in lines:
        if line.startswith("+++ b/"):
            file_name = line.split("+++ b/")[1]
            files[file_name] = ""
        elif line.startswith("+") and not line.startswith("+++"):
            files[file_name] += " "+line.split("+")[1].strip()
    return files

def processFiles(uuid, repo, email, check_skipped, files) -> int:
    """
    Returns exit_code: 1 if credentials are found, 0 if not.
    :param uuid The hook execution id
    :param repo The repository
    :param email The user's git email
    :param check_skipped True if the check is skipped, this means the analysis is done, but if there are any errors or credentials found, the hook still ends successfully.
    :param files The dictionary of file:new_content
    """
    files_array = processFilesDictionary(files)
    i = 0
    lenght = len(files_array)
    credentials_found = False

    while i*CONST_PAGE_SIZE < lenght:
        credentials_found = checkCredentials(i, uuid, repo, email, check_skipped,files_array[i*CONST_PAGE_SIZE:(i+1)*CONST_PAGE_SIZE], credentials_found) or credentials_found
        i+=1

    if credentials_found:
        print(f"\n{bold}{red}Please remove all the credentials detected and then try commit again.\nIf you think this is a False Positive, re run as follows: `skip_credentials_check=true git commit ...`\nMore information can be found in the official documentation: https://furydocs.io/sast-precommit//guide.\nIf you have any question about false positives create a ticket on Fury Support Precommit > Websec Hook > False Positive.{reset}")
        return 1
    return 0

def processFilesDictionary(files):
    """
    Returns the dictionary converted in a list of objects: [{name, content}]
    :param files The dictionary of file:new_content
    """
    response = []
    for file_name in files:
        content = files[file_name]
        if len(content) > 0:
            if len(content) > MAX_SIZE:
                response.extend(processLargeFile(file_name, content, MAX_SIZE))
            else:
                response.append({"name": file_name, "content": content.strip()})
    return response


def processLargeFile(file_name, content, max_size):
    response = []
    content_size = len(content)
    idx_from = 0
    idx_to = max_size
    
    while idx_to < content_size+max_size and idx_to > 0: # if we reached idx_to == 0, then we have NO blank space in the first 100KB
        if idx_to >= content_size: # if idx_to >= content_size -> we reached the end of the file content.
            response.append({"name":file_name, "content":content[idx_from:idx_to].strip()})
            break
        
        if content[idx_to] not in string.whitespace: # separating the file by blank spaces
            idx_to-=1 # if the actual index is not a blank space the index goes back one place
        else:
            response.append({"name":file_name, "content":content[idx_from:idx_to].strip()})
            idx_from = idx_to # now we move the idx_from to the place the idx_to was.
            idx_to += max_size # we increment idx_to by max_size
    return response

    

def checkCredentials(idx, uuid, repo, email, check_skipped,files, credentials_already_found) -> bool:
    """
    Returns if credentials are found in any of the files analyzed.
    :param idx The index -> the page being analyzed.
    :param uuid The hook execution id
    :param repo The repository
    :param email The user's git email
    :param check_skipped True if the check is skipped, this means the analysis is done, but if there are any errors or credentials found, the hook still ends successfully.
    :param files The dictionary of file:new_content
    :param credentials_already_found True if credentials were already found in previous pages.
    """
    payload = {"page":idx+1,"id":str(uuid), "repository":repo, "email":email, "check_skipped": check_skipped, "files": files, "version": version}
    res = make_request("POST", precommit_url, payload)
    
    if len(res) != 0 and not credentials_already_found:
        print("Credentials found in the following files:")

    for result in res:
        printResults(result["file"], result["findings"])
    return len(res) != 0

def printResults(file, findings):
    """
    Prints formatted the file and its findings
    :param file The file name
    :param finding List of datatype and findings
    """
    print(f"\n{cyan}{file}{reset}")
    for finding in findings:
        datatype = finding["datatype"]
        for credential in finding["findings"]:
            print(f"- {datatype}: {soft_white}{credential}{reset}")

if __name__ == '__main__':
    raise SystemExit(main())