from importlib import import_module
import os
import json
import sys
import argparse

from message_conversion.java_class_spec import JavaClassSpec
from message_conversion.generate_spec import (
    filter_unique_objects,
    java_class_spec_generator,
)
from message_conversion.code_artifacts import generate_java_code_from_spec


def write_java_file(root_path: str, relative_path: str, code: str) -> None:
    abs_path = os.path.join(root_path, relative_path)
    abs_dir = os.path.dirname(abs_path)
    if not os.path.isdir(abs_dir):
        os.makedirs(abs_dir)
    print(f"Writing to {abs_path}")
    with open(abs_path, "w") as file:
        file.write(code)


def generate_from_messages(root_path, messages):
    unique_objects = {}
    for msg in messages:
        class_spec = JavaClassSpec(msg._type)
        java_class_spec_generator(class_spec, msg)
        filter_unique_objects(unique_objects, class_spec)
    for spec in unique_objects.values():
        relative_path, code = generate_java_code_from_spec(root_path, spec)
        write_java_file(root_path, relative_path, code)
    return unique_objects


def import_sources(source_file_path: str):
    with open(source_file_path) as file:
        sources = json.load(file)["sources"]
    messages = []
    for source in sources:
        connection_header = source.split("/")
        ros_pkg = connection_header[0] + ".msg"
        msg_type = connection_header[1]
        msg_class = getattr(import_module(ros_pkg), msg_type)
        message = msg_class()
        messages.append(message)
    return messages


def main():
    parser = argparse.ArgumentParser(description='publish_landmark')
    parser.add_argument(
        "--root", "-r", default="../src/main/java", type=str, help="Java project root"
    )
    parser.add_argument(
        "--messages", "-m", default="frc/team88/ros/messages", type=str, help="Messages destination subdirectory"
    )
    parser.add_argument(
        "--sources", "-s", default="./source_list.json", type=str, help="List of message connection headers to generate"
    )
    args = parser.parse_args()

    java_root = os.path.abspath(args.root)
    root_path = args.messages
    sources_file_path = os.path.abspath(args.sources)
    os.chdir(java_root)
    messages = import_sources(sources_file_path)
    generate_from_messages(root_path, messages)


if __name__ == "__main__":
    main()