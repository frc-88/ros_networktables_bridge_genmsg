import os
import argparse
import json
from typing import List
from dataclasses import dataclass


@dataclass
class RepositoryInfo:
    local_name: str
    uri: str
    version: str


def import_repos(source_file_path: str) -> List[RepositoryInfo]:
    """
    Imports repository info from a JSON file.

    :param source_file_path: The path to the JSON file containing the repos.
    :return: A list of objects containing info about the specified repos.
    """
    # Open the JSON file and load the "sources" key
    with open(source_file_path) as file:
        repos = json.load(file)["repos"]

    # iterate over the repos and store them in an object
    infos = []
    for repo in repos:
        info = RepositoryInfo(
            repo["local-name"],
            repo["uri"],
            repo["version"]
        )
        infos.append(info)
    return infos


def is_bash():
    return "bash" in os.environ["SHELL"]


def exec_clone(url: str, branch: str, destination: str) -> None:
    if os.path.isdir(destination):
        print(f"{url} already exists locally")
        return
    if is_bash():
        os.system(f"git clone {url} -b {branch} {destination}")
    else:
        os.system(f"git \"clone\" {url} /b {branch} \"{destination}\"")


def clone(repos: List[RepositoryInfo], destination: str) -> None:
    for repo in repos:
        path = os.path.join(destination, repo.local_name)
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
