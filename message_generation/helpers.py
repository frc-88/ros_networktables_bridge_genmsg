import os
import json
import platform
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
        info = RepositoryInfo(repo["local-name"], repo["uri"], repo["version"])
        infos.append(info)
    return infos


def is_bash():
    return "bash" in os.environ.get("SHELL", "")


def is_windows():
    return platform.system() == "Windows"
