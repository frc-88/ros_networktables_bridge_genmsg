import re
from importlib import import_module
from typing import Dict, List, Type

from .ros_message import RosMessage
from .constants import ROS_TO_JAVA_PRIMITIVE_MAPPING, RosPrimitive
from .java_class_spec import JavaClassSpec, JavaTimeSpec, JavaDurationSpec

MsgClassCacheMap = Dict[str, Type[RosMessage]]
MSG_CLASS_CACHE: MsgClassCacheMap = {}


def get_msg_class(cache: MsgClassCacheMap, msg_type_name: str):
    """
    Retrieves the ROS message class for a given message type name.

    :param cache: A cache to store previously imported ROS message classes.
    :param msg_type_name: The message type name.
    :return: The ROS message class for the given message type name.
    """
    if msg_type_name not in cache:
        connection_header = msg_type_name.split("/")
        if len(connection_header) != 2:
            raise ValueError(f"Invalid connection header: {msg_type_name}")
        ros_pkg = connection_header[0] + ".msg"
        msg_type = connection_header[1]

        # import the ROS message module.
        # ex. 'nav_msgs/Odometry' is equivalent to `from nav_msgs.msg import Odometry`
        msg_class = getattr(import_module(ros_pkg), msg_type)
        cache[msg_type_name] = msg_class
    return cache[msg_type_name]


def is_msg_type_list(msg_type_name: str) -> bool:
    """
    Determines if the given message type name represents a list.

    :param msg_type_name: The message type name.
    :return: True if the message type name represents a list, False otherwise.
    """
    return msg_type_name.endswith("]")


def get_list_size(msg_type_name: str) -> int:
    """
    Extracts the size of the list from the given message type name.
    ROS list messages come in the format `package/data_type[size]`

    :param msg_type_name: The message type name.
    :return: The size of the list, or 0 if the message type name does not represent a list.
    """
    pattern = r"^.+\[(\d+)\]"
    match = re.search(pattern, msg_type_name)
    if match is None:
        return 0
    else:
        return int(match.group(1))


def get_list_type(msg_type_name: str) -> str:
    """
    Extracts the base type of the list from the given message type name.
    ROS list messages come in the format `package/data_type[size]`

    :param msg_type_name: The message type name.
    :return: The base type of the list, or the original message type name if it does not represent a list.
    """
    if is_msg_type_list(msg_type_name):
        index = msg_type_name.rfind("[")
        return msg_type_name[:index]
    else:
        return msg_type_name


def get_message_constants(msg_instance: RosMessage):
    """
    Extracts the constants from a ROS message instance.

    :param msg_instance: The instance of a ROS message class.
    :return: A dictionary containing the constants of the ROS message.
    """
    # Get the set of slots (field names) for the message instance
    slots = set(msg_instance.__slots__)

    # Iterate through the attributes of the message class and filter out private attributes and callables
    props = []
    for name, value in vars(msg_instance.__class__).items():
        if name.startswith("_"):
            continue
        if callable(value):
            continue
        props.append(name)

    # Calculate the set difference between the attributes and slots to find the constants
    constants = set(props).difference(slots)

    # Create a dictionary to store the constants and their values
    constants_map = {}
    for name in props:  # iterating over the list preserves the order
        if name in constants:
            constants_map[name] = getattr(msg_instance, name)

    return constants_map


def java_class_spec_generator(class_spec: JavaClassSpec, msg_instance: RosMessage):
    """
    Generates a Java class specification based on a ROS message instance.
    If the ROS message contains other ROS messages, recursively generate a Java class
    specification for those sub messages.

    :param class_spec: A JavaClassSpec object to be populated with the properties of the ROS message.
    :param msg_instance: A ROS message instance to be converted to a Java class specification.
    """
    # Iterate through the ROS message properties and their data types
    for name, data_type in zip(msg_instance.__slots__, msg_instance._slot_types):
        # name is the field name of the ROS message. ex. 'pose' for PoseStamped
        # data_type is the ROS message data type. ex. geometry_msgs/Pose for PoseStamped.pose

        # Check if the data type is a list, and if so, get its size and type
        if is_msg_type_list(data_type):
            size = get_list_size(data_type)
            data_type = get_list_type(data_type)
        else:
            size = -1

        # Try to convert the data type to a ROS primitive type
        try:
            data_primitive = RosPrimitive(data_type)
        except ValueError:
            data_primitive = None

        # Get the current property value from the ROS message instance
        value = getattr(msg_instance, name)

        # If the data type is not a ROS primitive type, generate a sub-class specification
        if data_primitive is None:
            msg_class = get_msg_class(MSG_CLASS_CACHE, data_type)
            sub_class_spec = class_spec.add_sub_msg(name, data_type, size)
            java_class_spec_generator(sub_class_spec, msg_class())
        # If the data type is a ROS time primitive, add a JavaTimeSpec to the class specification
        elif data_primitive == RosPrimitive.time:
            class_spec.add_sub_spec(name, JavaTimeSpec())
        # If the data type is a ROS duration primitive, add a JavaDurationSpec to the class specification
        elif data_primitive == RosPrimitive.duration:
            class_spec.add_sub_spec(name, JavaDurationSpec())
        # Otherwise, add a field to the class specification with the appropriate Java primitive type
        else:
            class_spec.add_field(
                name, value, ROS_TO_JAVA_PRIMITIVE_MAPPING[data_primitive], size
            )

    # Add constants from the ROS message to the Java class specification
    for name, value in get_message_constants(msg_instance).items():
        class_spec.add_constant(name, value)


def filter_unique_objects(
    unique_objects: Dict[str, JavaClassSpec],
    class_spec: JavaClassSpec,
    blacklist: List[str],
):
    """
    Recursively filters Java class specifications to keep only unique objects, excluding those in the blacklist.

    :param unique_objects: A dictionary to store unique Java class specifications.
    :param class_spec: The Java class specification to be checked for uniqueness.
    :param blacklist: A list of message types to be excluded from the unique objects.
    """
    # If the message type of the class_spec is in the blacklist, return immediately
    if class_spec.msg_type in blacklist:
        return

    # If the message type of the class_spec is already in the unique_objects, check if they are equal
    if class_spec.msg_type in unique_objects:
        assert unique_objects[class_spec.msg_type] == class_spec, (
            "Found class specs that don't match: %s != %s"
            % (unique_objects[class_spec.msg_type], class_spec)
        )
    # If the message type is not in unique_objects, add it
    else:
        unique_objects[class_spec.msg_type] = class_spec

    # Recursively filter the unique objects for fields of type JavaClassSpec
    for field in class_spec.fields.values():
        if type(field) == JavaClassSpec:
            filter_unique_objects(unique_objects, field, blacklist)
