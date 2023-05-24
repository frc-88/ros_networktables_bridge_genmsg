import os
import shutil
import argparse
import urllib.parse
from typing import List

from message_generation.helpers import is_bash, import_repos, RepositoryInfo


def exec_clone(url: str, branch: str, destination: str) -> None:
    if os.path.isdir(destination):
        print(f"{url} already exists locally")
        return
    print(f"Cloning {url} to {destination}")
    if is_bash():
        os.system(f"git clone {url} -b {branch} {destination}")
    else:
        os.system(f'git "clone" {url} /b {branch} "{destination}"')


def exec_copy(path: str, destination: str) -> None:
    if os.path.isdir(destination):
        shutil.rmtree(destination)
    print(f"Copying {path} to {destination}")
    shutil.copytree(path, destination)


def clone(repos: List[RepositoryInfo], destination: str) -> None:
    for repo in repos:
        path = os.path.join(destination, repo.local_name)
        result = urllib.parse.urlsplit(repo.uri)
        if result.scheme == "file":
            exec_copy(result.path, path)
        else:
            exec_clone(repo.uri, repo.version, path)


def main():
    parser = argparse.ArgumentParser(description="clone_repos")
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
    clone(repos, destination)


if __name__ == "__main__":
    main()
