from importlib import import_module
import os
import json
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


def generate_from_messages(root_path, messages, default_messages, external_package):
    blacklist = [msg._type for msg in default_messages]
    unique_objects = {}
    for msg in messages:
        class_spec = JavaClassSpec(msg._type)
        java_class_spec_generator(class_spec, msg)
        filter_unique_objects(unique_objects, class_spec, blacklist)
    for spec in unique_objects.values():
        relative_path, code = generate_java_code_from_spec(root_path, spec, external_package + ".messages.", blacklist)
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_source_list = f"{base_dir}/source_list.json"

    parser = argparse.ArgumentParser(description="generate_java_messages")
    parser.add_argument(
        "--root", "-r", default="../src/main/java", type=str, help="Java project root"
    )
    parser.add_argument(
        "--messages", "-m", default="frc/team88/ros/messages", type=str, help="Messages destination subdirectory"
    )
    parser.add_argument(
        "--sources", "-s", default="", type=str, help="List of message connection headers to generate"
    )
    args = parser.parse_args()

    java_root = os.path.abspath(args.root)
    root_path = args.messages
    if len(args.sources) == 0:
        sources_file_path = default_source_list
        default_messages = []
    else:
        sources_file_path = os.path.abspath(args.sources)
        default_messages = import_sources(default_source_list)

    external_package = "frc.team88.ros"

    messages = import_sources(sources_file_path)

    os.chdir(java_root)
    generate_from_messages(root_path, messages, default_messages, external_package)


if __name__ == "__main__":
    main()
