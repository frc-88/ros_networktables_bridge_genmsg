from dataclasses import dataclass
from typing import Dict, Union

from .constants import JavaPrimitive, PythonPrimitive


@dataclass
class JavaMessageField:
    """
    Represents a Java class primitive field and its corresponding value.
    size is -1 for not a list, 0 for a variable list, >0 for a fixed size list.
    """

    value: PythonPrimitive
    msg_type: JavaPrimitive
    size: int


class JavaClassSpec:
    def __init__(self, msg_type_name: str, size=-1) -> None:
        """
        Initializes a JavaClassSpec object.

        :param msg_type_name: The message type name.
        :param size: The size of the list, -1 for not a list, 0 for a variable list, >0 for a fixed size list.
        """
        self.fields: Dict[str, Union[JavaMessageField, JavaClassSpec]] = {}
        self.constants: Dict[str, PythonPrimitive] = {}
        self.msg_type = msg_type_name
        self.size = size

    def add_constant(self, name: str, value: PythonPrimitive) -> None:
        """
        Adds a constant to the class specification.

        :param name: The name of the constant.
        :param value: The value of the constant.
        """
        self.constants[name] = value

    def add_field(
        self, name: str, value: PythonPrimitive, msg_type: JavaPrimitive, size=-1
    ) -> None:
        """
        Adds a field to the class specification.

        :param name: The name of the field.
        :param value: The value of the field.
        :param msg_type: The Java primitive type of the field.
        :param size: The size of the list, -1 for not a list, 0 for a variable list, >0 for a fixed size list.
        """
        # Add a new JavaMessageField to the fields dictionary
        self.fields[name] = JavaMessageField(value, msg_type, size)

    def add_sub_msg(self, name: str, msg_type_name: str, size=-1) -> "JavaClassSpec":
        """
        Adds a submessage to the class specification.

        :param name: The name of the submessage.
        :param msg_type_name: The message type name of the submessage.
        :param size: The size of the list, -1 for not a list, 0 for a variable list, >0 for a fixed size list.
        :return: The created JavaClassSpec for the submessage.
        """
        # Create a new JavaClassSpec object for the submessage
        spec = JavaClassSpec(msg_type_name, size)
        # Add the new JavaClassSpec to the fields dictionary
        self.add_sub_spec(name, spec)
        return spec

    def add_sub_spec(self, name: str, spec: "JavaClassSpec"):
        """
        Adds a submessage specification to the class specification.

        :param name: The name of the submessage.
        :param spec: The JavaClassSpec object for the submessage.
        """
        # Add the JavaClassSpec to the fields dictionary
        self.fields[name] = spec

    def _to_str(self, indent=0, tab_size=4) -> str:
        """
        Convert JavaClassSpec object to str for debug purposes. Does not generate Java code.

        :return: A string containing all the names and properties formatted for human readability.
        """
        indent += 1
        field_indent_str = " " * (indent * tab_size)
        string = f"{self.msg_type}:\n"
        for name, value in self.fields.items():
            if type(value) == JavaMessageField:
                string += f"{field_indent_str}{name}: {value}\n"
            elif isinstance(value, JavaClassSpec):
                string += f"{field_indent_str}{name} {value._to_str(indent)}"
            else:
                raise ValueError(f"Invalid object found in fields: {value}")
        return string

    def __eq__(self, __value: object) -> bool:
        """
        Check if this object is equivalent to another.
        If the other object is not JavaClassSpec, they are not equal.
        Otherwise, check if all the fields and values match.
        """
        if type(__value) == JavaClassSpec:
            if self.fields.keys() != __value.fields.keys():
                return False
            for name, field in self.fields.items():
                other_field = __value.fields[name]
                if type(field) != type(other_field):
                    return False
                if type(field) == JavaMessageField and (
                    field.value != other_field.value
                    or field.msg_type != other_field.msg_type
                ):  # type: ignore
                    return False
                elif type(field) == JavaClassSpec and field != other_field:
                    return False
            return True
        else:
            return False

    def __repr__(self) -> str:
        return self._to_str()


class JavaTimeSpec(JavaClassSpec):
    def __init__(self) -> None:
        super().__init__("Time", -1)

        self.add_field("secs", 0, JavaPrimitive.int, -1)
        self.add_field("nsecs", 0, JavaPrimitive.int, -1)


class JavaDurationSpec(JavaClassSpec):
    def __init__(self) -> None:
        super().__init__("Duration", -1)

        self.add_field("secs", 0, JavaPrimitive.int, -1)
        self.add_field("nsecs", 0, JavaPrimitive.int, -1)
