import subprocess
import sys

from isort import (
    SortImports,
)
from isort.hooks import (
    get_lines,
    get_output,
)


"""
Original Isort hook was processing only .py files
In our case we need to process also files like "caas"
So patched version of the hook is below, it addtitionally checks
"file --mime-type <modified_file> | grep text/x-python"
"""


def git_hook(strict=False):
    """
    Git pre-commit hook to check staged files for isort errors
    :param bool strict - if True, return number of errors on exit,
        causing the hook to fail. If False, return zero so it will
        just act as a warning.
    :return number of errors if in strict mode, 0 otherwise.
    """

    # Get list of files modified and staged
    diff_cmd = \
        "git diff-index --cached --name-only --diff-filter=ACMRTUXB HEAD"
    files_modified = get_lines(diff_cmd)
    errors = 0
    for filename in files_modified:
        typecheck_cmd = "file --mime-type {} | grep text/x-python >/dev/null" \
            .format(filename)
        if filename.endswith('.py') or \
           subprocess.call(typecheck_cmd, shell=True) == 0:
            # Get the staged contents of the file
            staged_cmd = "git show :%s" % filename
            staged_contents = get_output(staged_cmd)

            sort = SortImports(
                file_path=filename,
                file_contents=staged_contents.decode(),
                check=True
            )

            if sort.incorrectly_sorted:
                errors += 1

    if errors:
        print('Run "isort <path_to_file>" to solve automatically')
    return errors if strict else 0


if __name__ == '__main__':
    sys.exit(git_hook(strict=True))
