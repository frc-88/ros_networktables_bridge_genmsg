from importlib import import_module
import os
import json
import argparse
from typing import Iterable, List

from message_conversion.ros_message import RosMessage
from message_conversion.java_class_spec import JavaClassSpec
from message_conversion.generate_spec import (
    filter_unique_objects,
    java_class_spec_generator,
)
from message_conversion.code_artifacts import generate_java_code_from_spec


def write_java_file(root_path: str, relative_path: str, code: str) -> None:
    """
    Writes the generated Java code to a file at the specified path.

    :param root_path: The root path where the file should be created.
    :param relative_path: The relative path from the root path to the target file.
    :param code: The Java code to be written to the file.
    """
    # Create an absolute path by joining the root and relative paths
    abs_path = os.path.join(root_path, relative_path)
    # Determine the directory containing the target file
    abs_dir = os.path.dirname(abs_path)

    # Check if the directory exists, if not, create it
    if not os.path.isdir(abs_dir):
        os.makedirs(abs_dir)

    # Print the absolute path of the file being written
    print(f"Writing to {abs_path}")

    # Open the file in write mode and write the Java code to it
    with open(abs_path, "w") as file:
        file.write(code)


def generate_from_messages(
    root_path: str,
    messages: Iterable[RosMessage],
    default_messages: Iterable[RosMessage],
    external_package: str,
):
    """
    Generates Java code from ROS message specifications.

    :param root_path: The root path where the Java files should be created.
    :param messages: An iterable of ROS messages to be processed.
    :param default_messages: An iterable of ROS messages already generated in 
        ROSNetworkTablesBridge (skip these messages).
    :param external_package: The package name for the generated Java code.
    :return: A dictionary of unique Java class specifications.
    """
    # Create a blacklist of default ROS message types
    blacklist = [msg._type for msg in default_messages]

    # Initialize a dictionary to store unique Java class specifications
    unique_objects = {}

    # Generate Java class specifications for each ROS message
    for msg in messages:
        class_spec = JavaClassSpec(msg._type)
        java_class_spec_generator(class_spec, msg)
        filter_unique_objects(unique_objects, class_spec, blacklist)

    # Generate Java code for each unique Java class specification
    for spec in unique_objects.values():
        relative_path, code = generate_java_code_from_spec(
            root_path, spec, external_package + ".messages.", blacklist
        )
        # Write the generated Java code to a file
        write_java_file(root_path, relative_path, code)

    return unique_objects


def import_sources(source_file_path: str) -> List[RosMessage]:
    """
    Imports ROS message sources from a JSON file.

    :param source_file_path: The path to the JSON file containing the sources.
    :return: A list of ROS messages imported from the specified sources.
    """
    # Open the JSON file and load the "sources" key
    with open(source_file_path) as file:
        sources = json.load(file)["sources"]

    # Initialize a list to store the imported ROS messages
    messages = []

    # Iterate through the sources and import the corresponding ROS messages
    for source in sources:
        # Split the source string into ROS package and message type
        connection_header = source.split("/")
        ros_pkg = connection_header[0] + ".msg"
        msg_type = connection_header[1]

        # Import the ROS message class
        msg_class = getattr(import_module(ros_pkg), msg_type)

        # Create a new instance of the ROS message class and add it to the list
        message = msg_class()
        messages.append(message)

    return messages


def main():
    # Get the base directory of the script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_source_list = f"{base_dir}/source_list.json"

    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(description="generate_java_messages")
    parser.add_argument(
        "--root", "-r", default="../src/main/java", type=str, help="Java project root"
    )
    parser.add_argument(
        "--messages",
        "-m",
        default="frc/team88/ros/messages",
        type=str,
        help="Messages destination subdirectory",
    )
    parser.add_argument(
        "--sources",
        "-s",
        default="",
        type=str,
        help="List of message connection headers to generate",
    )
    args = parser.parse_args()

    # Parse command-line arguments
    java_root = os.path.abspath(args.root)
    root_path = args.messages
    if len(args.sources) == 0:
        # assume we're generating messages packaged with main library
        sources_file_path = default_source_list
        default_messages = []
    else:
        # we're generating custom messages provided by the user
        sources_file_path = os.path.abspath(args.sources)
        default_messages = import_sources(default_source_list)

    # the java package name of ROSNetworkTablesBridge
    external_package = "frc.team88.ros"

    # Import sources from the specified file path
    messages = import_sources(sources_file_path)

    # Change the current working directory to the Java project root
    os.chdir(java_root)

    # Generate Java code from the ROS messages
    generate_from_messages(root_path, messages, default_messages, external_package)


if __name__ == "__main__":
    main()
