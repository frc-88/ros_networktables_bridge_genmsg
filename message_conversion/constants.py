from enum import Enum
from typing import Union


class JavaPrimitive(Enum):
    # An enumeration of Java type primitives
    boolean = "boolean"
    byte = "byte"
    char = "char"
    short = "short"
    int = "int"
    long = "long"
    float = "float"
    double = "double"
    String = "java.lang.String"


class RosPrimitive(Enum):
    # An enumeration of ROS primitive data types.
    # See this wiki page for reference: http://wiki.ros.org/msg#Fields
    bool = "bool"
    byte = "byte"
    char = "char"
    int8 = "int8"
    uint8 = "uint8"
    int16 = "int16"
    uint16 = "uint16"
    int32 = "int32"
    uint32 = "uint32"
    int64 = "int64"
    uint64 = "uint64"
    float32 = "float32"
    float64 = "float64"
    string = "string"
    time = "time"
    duration = "duration"


PythonPrimitive = Union[bool, bytes, int, float, str]

ROS_TO_JAVA_PRIMITIVE_MAPPING = {
    # A conversion mapping from ROS to Java primitives
    RosPrimitive.bool: JavaPrimitive.boolean,
    RosPrimitive.int8: JavaPrimitive.byte,
    RosPrimitive.byte: JavaPrimitive.byte,
    RosPrimitive.char: JavaPrimitive.char,
    RosPrimitive.uint8: JavaPrimitive.char,
    RosPrimitive.int16: JavaPrimitive.short,
    RosPrimitive.uint16: JavaPrimitive.short,
    RosPrimitive.int32: JavaPrimitive.int,
    RosPrimitive.uint32: JavaPrimitive.int,
    RosPrimitive.int64: JavaPrimitive.long,
    RosPrimitive.uint64: JavaPrimitive.long,
    RosPrimitive.float32: JavaPrimitive.float,
    RosPrimitive.float64: JavaPrimitive.double,
    RosPrimitive.string: JavaPrimitive.String,
    RosPrimitive.time: JavaPrimitive.long,
    RosPrimitive.duration: JavaPrimitive.long,
}
PYTHON_TO_JAVA_PRIMITIVE_MAPPING = {
    # A conversion mapping from Python to Java primitives
    bool: JavaPrimitive.boolean,
    int: JavaPrimitive.int,
    float: JavaPrimitive.double,
    str: JavaPrimitive.String,
    # this may be a problem if there are constants defined with bytes
    bytes: JavaPrimitive.String,
}
PRIMITIVE_DEFAULTS = {
    # Java primitive default values
    JavaPrimitive.boolean: "false",
    JavaPrimitive.byte: "0",
    JavaPrimitive.char: "'\0'",
    JavaPrimitive.short: "0",
    JavaPrimitive.int: "0",
    JavaPrimitive.long: "0",
    JavaPrimitive.float: "0.0f",
    JavaPrimitive.double: "0.0",
    JavaPrimitive.String: '""',
}

PRIMITIVE_TO_JAVA_OBJECT = {
    # Java primitive to object mapping
    JavaPrimitive.boolean: "java.lang.Boolean",
    JavaPrimitive.byte: "java.lang.Byte",
    JavaPrimitive.char: "java.lang.Character",
    JavaPrimitive.short: "java.lang.Short",
    JavaPrimitive.int: "java.lang.Integer",
    JavaPrimitive.long: "java.lang.Long",
    JavaPrimitive.float: "java.lang.Float",
    JavaPrimitive.double: "java.lang.Double",
    JavaPrimitive.String: "java.lang.String",
}
JAVA_OBJECT_TO_PRIMITIVE = {v: k for k, v in PRIMITIVE_TO_JAVA_OBJECT.items()}
PRIMITIVE_JSON_FUNCTIONS = {
    # JSON to Java primitive conversion code snippets
    JavaPrimitive.boolean: "{obj}.getAsBoolean()",
    JavaPrimitive.byte: "{obj}.getAsByte()",
    JavaPrimitive.char: "(char){obj}.getAsByte()",
    JavaPrimitive.short: "{obj}.getAsShort()",
    JavaPrimitive.int: "{obj}.getAsInt()",
    JavaPrimitive.long: "{obj}.getAsLong()",
    JavaPrimitive.float: "{obj}.getAsFloat()",
    JavaPrimitive.double: "{obj}.getAsDouble()",
    JavaPrimitive.String: "{obj}.getAsString()",
}
