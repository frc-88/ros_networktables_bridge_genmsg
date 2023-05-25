import os
import argparse
from typing import List

from message_generation.helpers import import_repos, is_bash, is_windows, RepositoryInfo

# skip building these packages since they're already installed
SPECIAL_NAMES = [
    "std_msgs",
    "common_msgs",
]


def exec_rospy_build(package_directory, gen_msg_root) -> None:
    if is_bash():
        os.system(f"rospy-build genmsg {package_directory} -s {gen_msg_root}")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.system(
            f'{base_dir}\\venv\\Scripts\\rospy-build "genmsg" '
            f'"{package_directory}" "-s" "{gen_msg_root}"'
        )


def exec_pip_install(package_directory: str) -> None:
    if is_bash():
        os.system(f"python3 -m pip install -e {package_directory}")
    else:
        os.system(f'python "-m" "pip" "install" "-e" "{package_directory}"')


def find_package_dir(root: str) -> str:
    for dirpath, dirnames, filenames in os.walk(root):
        if "msg" in dirnames:
            return dirpath
    return ""


def append_to_python_path(path: str) -> None:
    pythonpath = os.environ.get("PYTHONPATH", "").strip()
    if len(pythonpath) != 0 and pythonpath[0] != ":":
        if is_windows():
            pythonpath = ";" + pythonpath
        else:
            pythonpath = ":" + pythonpath
    os.environ["PYTHONPATH"] = path + pythonpath


def save_python_path(file_path: str) -> None:
    pythonpath = os.environ.get("PYTHONPATH", "")
    if is_windows():
        batch_file_path = file_path + ".bat"
        batch_command = f"SET PYTHONPATH={pythonpath}"
        with open(batch_file_path, "w") as file:
            file.write(batch_command)
    else:
        bash_file_path = file_path + ".sh"
        bash_command = f"export PYTHONPATH={pythonpath}"
        with open(bash_file_path, "w") as file:
            file.write(bash_command)


def generate_rospy_messages(repos: List[RepositoryInfo], gen_msg_root: str) -> None:
    if not os.path.isdir(gen_msg_root):
        os.makedirs(gen_msg_root)
    for repo in repos:
        if repo.local_name in SPECIAL_NAMES:
            continue
        path = os.path.join(gen_msg_root, repo.local_name)
        package_dir = find_package_dir(path)
        if len(package_dir) == 0:
            print(f"No message directory found in {repo.local_name}. Skipping.")
            continue
        append_to_python_path(package_dir)
        exec_rospy_build(package_dir, gen_msg_root)
        exec_pip_install(package_dir)
    save_python_path(os.path.join(gen_msg_root, "set_build_python_path"))


def main():
    parser = argparse.ArgumentParser(description="generate_messages")
    parser.add_argument(
        "sources",
        type=str,
        help="Sources info",
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Clone destination directory",
    )
    args = parser.parse_args()

    sources = args.sources
    destination = args.destination

    repos = import_repos(sources)
    generate_rospy_messages(repos, destination)


if __name__ == "__main__":
    main()
