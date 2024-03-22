import os
import re
from dataclasses import dataclass
from typing import List, Tuple
from .constants import (
    JAVA_OBJECT_TO_PRIMITIVE,
    PRIMITIVE_DEFAULTS,
    PRIMITIVE_JSON_FUNCTIONS,
    PRIMITIVE_TO_JAVA_OBJECT,
    PYTHON_TO_JAVA_PRIMITIVE_MAPPING,
    JavaPrimitive,
)
from .java_class_spec import JavaClassSpec, JavaMessageField


def camel_case(snake_str: str) -> str:
    """
    Converts a snake_case (words separated by _) or
    kebab-case (words separated by -) string to a
    camelCase (words separated by capital letters) string.

    :param snake_str: a string
    :return: a string formatted in camelCase
    """
    camel_str = re.sub(r"(_|-)+", " ", snake_str).title().replace(" ", "")
    return camel_str[0].lower() + camel_str[1:]


@dataclass
class GeneratedCodeArtifacts:
    """
    A dataclass containing pieces of Java code to be inserted
    into the larger Java file.
    """

    fields_code: str  # non-static member fields code
    arg: str  # constructor arguments
    arg_assignment: str  # constructor argument assignment
    getter: str  # getter method
    setter: str  # setter method
    json_constructor: str  # JSON builder code


def get_full_type(package_root: str, field: JavaClassSpec) -> str:
    """
    Get the message's full Java type.
    ex. a JavaClassSpec generated from nav_msgs/Odometry becomes
    frc.team88.ros.messages.nav_msgs.Odometry

    :param package_root: root Java package name. ex. frc.team88.ros.messages.
    :param field: JavaClassSpec object to generate a full type from.
    :return: full Java type.
    """
    field_java_type = field.msg_type.replace("/", ".")
    if "." in field_java_type:
        package, class_name = field_java_type.split(".")
        class_name = get_class_special_case_package(package, class_name)
        field_java_type = f"{package}.{class_name}"
    full_type = f"{package_root}{field_java_type}"
    return full_type


INDENT = " " * 4


def getter_template(full_type: str, name: str) -> str:
    """
    Java code template for a getter method.

    :param full_type: the Java class' full type. See get_full_type()
    :param name: the name of the field.
    :return: Java code for the getter
    """
    return f"""{INDENT}public {full_type} {camel_case('get_' + name)}() {{
        return this.{name};
    }}
"""


def setter_template(full_type: str, name: str) -> str:
    """
    Java code template for a setter method.

    :param full_type: the Java class' full type. See get_full_type()
    :param name: the name of the field.
    :return: Java code for the setter
    """
    return f"""{INDENT}public void {camel_case('set_' + name)}({full_type} {name}) {{
        this.{name} = {name};
    }}
"""


def generate_code_from_field(
    imports: set, package_root: str, name: str, field: JavaMessageField
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for the generated code.
    :param name: Field name.
    :param field: JavaMessageField object containing field information.
    :return: GeneratedCodeArtifacts containing code snippets for the field.
    """
    # Get the Java type of the field
    field_java_type = field.msg_type.value

    # Generate field declaration code snippet
    fields_code = f"{INDENT}private {field_java_type} {name} = {PRIMITIVE_DEFAULTS[field.msg_type]};\n"

    # Generate constructor argument code snippet
    arg = f"{field_java_type} {name}"

    # Generate constructor argument assignment code snippet
    arg_assignment = f"{INDENT * 2}this.{name} = {name};\n"

    # Generate getter method code snippet
    getter = getter_template(field_java_type, name)

    # Generate setter method code snippet
    setter = setter_template(field_java_type, name)

    # Generate JSON parsing code snippet
    json_parse = PRIMITIVE_JSON_FUNCTIONS[field.msg_type].format(
        obj=f'jsonObj.get("{name}")'
    )
    json_constructor = f"{INDENT * 2}this.{name} = {json_parse};\n"

    return GeneratedCodeArtifacts(
        fields_code=fields_code,
        arg=arg,
        arg_assignment=arg_assignment,
        getter=getter,
        setter=setter,
        json_constructor=json_constructor,
    )


def generate_code_from_arraylist_type(
    imports: set, name: str, full_type: str
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for an ArrayList field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param name: Field name.
    :param full_type: Full type of the ArrayList elements.
    :return: GeneratedCodeArtifacts containing code snippets for the ArrayList field.
    """
    # Add required imports for ArrayList, Arrays, and JsonElement
    imports.add("import java.util.ArrayList;")
    imports.add("import java.util.Arrays;")
    imports.add("import com.google.gson.JsonElement;")

    # Define the ArrayList type
    array_type = f"ArrayList<{full_type}>"

    # Determine the JSON parsing code based on the full_type
    if full_type in JAVA_OBJECT_TO_PRIMITIVE:
        primitive = JavaPrimitive(JAVA_OBJECT_TO_PRIMITIVE[full_type].value)
        new_from_json_code = PRIMITIVE_JSON_FUNCTIONS[primitive]
    else:
        new_from_json_code = f"new {full_type}({{obj}}.getAsJsonObject())"

    # Generate field declaration code snippet
    fields_code = f"{INDENT}private {array_type} {name} = new ArrayList<>();\n"

    # Generate constructor argument code snippet
    arg = f"{full_type}[] {name}"

    # Generate constructor argument assignment code snippet
    arg_assignment = (
        f"{INDENT * 2}this.{name} = new ArrayList<>(Arrays.asList({name}));\n"
    )

    # Generate getter method code snippet
    getter = getter_template(array_type, name)

    # Generate setter method code snippet
    setter = setter_template(array_type, name)

    # Generate JSON parsing code snippet for ArrayList elements
    json_constructor = f"""{INDENT * 2}for (JsonElement {name}_element : jsonObj.getAsJsonArray("{name}")) {{
{INDENT * 3}this.{name}.add({new_from_json_code.format(obj=f"{name}_element")});
{INDENT * 2}}}
"""

    return GeneratedCodeArtifacts(
        fields_code=fields_code,
        arg=arg,
        arg_assignment=arg_assignment,
        getter=getter,
        setter=setter,
        json_constructor=json_constructor,
    )


def generate_code_from_static_array_type(
    imports: set, name: str, full_type: str, size: int
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a static array field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param name: Field name.
    :param full_type: Full type of the static array elements.
    :param size: Size of the static array.
    :return: GeneratedCodeArtifacts containing code snippets for the static array field.
    """
    # Add required import for JsonElement
    imports.add("import com.google.gson.JsonElement;")

    # Initialize variables
    static_array_values = ""

    # Determine default value and JSON parsing code based on the full_type
    if full_type in JAVA_OBJECT_TO_PRIMITIVE:
        primitive = JavaPrimitive(JAVA_OBJECT_TO_PRIMITIVE[full_type].value)
        value = PRIMITIVE_DEFAULTS[primitive]
        new_value_code = str(value)
        new_from_json_code = PRIMITIVE_JSON_FUNCTIONS[primitive]
    else:
        new_value_code = f"new {full_type}()"
        new_from_json_code = f"new {full_type}({{obj}}.getAsJsonObject())"

    # Generate static array initialization values
    for index in range(size):
        static_array_values += f"\n{INDENT * 2}{new_value_code},"
    static_array_values = static_array_values[:-1] + "\n    "

    # Define the static array type
    array_type = f"{full_type}[]"

    # Generate field declaration code snippet
    fields_code = f"{INDENT}private {array_type} {name} = new {array_type} {{{static_array_values}}};\n"

    # Generate constructor argument code snippet
    arg = f"{array_type} {name}"

    # Generate constructor argument assignment code snippet
    arg_assignment = f"""{INDENT * 2}for (int index = 0; index < {size}; index++) {{
{INDENT * 3}this.{name}[index] = {name}[index];
{INDENT * 2}}}
"""

    # Generate getter method code snippet
    getter = getter_template(array_type, name)

    # Generate setter method code snippet
    setter = setter_template(array_type, name)

    # Generate JSON parsing code snippet for static array elements
    json_constructor = f"""        int {name}_element_index = 0;
        for (JsonElement {name}_element : jsonObj.getAsJsonArray("{name}")) {{
            this.{name}[{name}_element_index++] = {new_from_json_code.format(obj=f"{name}_element")};
        }}
"""

    return GeneratedCodeArtifacts(
        fields_code=fields_code,
        arg=arg,
        arg_assignment=arg_assignment,
        getter=getter,
        setter=setter,
        json_constructor=json_constructor,
    )


def generate_code_from_field_variable_list(
    imports: set, package_root: str, name: str, field: JavaMessageField
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a variable-length list field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for Java classes.
    :param name: Field name.
    :param field: JavaMessageField instance representing the field.
    :return: GeneratedCodeArtifacts containing code snippets for the variable-length list field.
    """
    # Call generate_code_from_arraylist_type to generate the code snippets
    return generate_code_from_arraylist_type(
        imports, name, PRIMITIVE_TO_JAVA_OBJECT[field.msg_type]
    )


def generate_code_from_field_static_list(
    imports: set, package_root: str, name: str, field: JavaMessageField
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a static-length list field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for Java classes.
    :param name: Field name.
    :param field: JavaMessageField instance representing the field.
    :return: GeneratedCodeArtifacts containing code snippets for the static-length list field.
    """
    # Call generate_code_from_static_array_type to generate the code snippets
    return generate_code_from_static_array_type(
        imports, name, PRIMITIVE_TO_JAVA_OBJECT[field.msg_type], field.size
    )


def generate_code_from_spec_sub_msg(
    imports: set, package_root: str, name: str, field: JavaClassSpec
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a sub-message field in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for Java classes.
    :param name: Field name.
    :param field: JavaClassSpec instance representing the field.
    :return: GeneratedCodeArtifacts containing code snippets for the sub-message field.
    """
    # Get the full type of the sub-message
    full_type = get_full_type(package_root, field)

    # Generate field declaration code snippet
    fields_code = f"{INDENT}private {full_type} {name} = new {full_type}();\n"

    # Generate constructor argument code snippet
    arg = f"{full_type} {name}"

    # Generate constructor argument assignment code snippet
    arg_assignment = f"{INDENT * 2}this.{name} = {name};\n"

    # Generate getter method code snippet
    getter = getter_template(full_type, name)

    # Generate setter method code snippet
    setter = setter_template(full_type, name)

    # Generate JSON parsing code snippet for sub-message
    json_constructor = f'{INDENT * 2}this.{name} = new {full_type}(jsonObj.get("{name}").getAsJsonObject());\n'

    return GeneratedCodeArtifacts(
        fields_code=fields_code,
        arg=arg,
        arg_assignment=arg_assignment,
        getter=getter,
        setter=setter,
        json_constructor=json_constructor,
    )


def generate_code_from_spec_variable_list(
    imports: set, package_root: str, name: str, field: JavaClassSpec
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a variable-length list field of a custom type in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for Java classes.
    :param name: Field name.
    :param field: JavaClassSpec instance representing the field.
    :return: GeneratedCodeArtifacts containing code snippets for the variable-length list field.
    """
    # Call generate_code_from_arraylist_type to generate the code snippets
    return generate_code_from_arraylist_type(
        imports, name, get_full_type(package_root, field)
    )


def generate_code_from_spec_static_list(
    imports: set, package_root: str, name: str, field: JavaClassSpec
) -> GeneratedCodeArtifacts:
    """
    Generates code artifacts for a static-length list field of a custom type in a Java class.

    :param imports: Set of imports. Required imports will be added to this set.
    :param package_root: Package root for Java classes.
    :param name: Field name.
    :param field: JavaClassSpec instance representing the field.
    :return: GeneratedCodeArtifacts containing code snippets for the static-length list field.
    """
    # Call generate_code_from_static_array_type to generate the code snippets
    return generate_code_from_static_array_type(
        imports, name, get_full_type(package_root, field), field.size
    )


def get_package_root(path: str) -> str:
    """
    Convert a path to a Java class package

    :param path: The path to the package.
    :return: The package root as a string.
    """
    # Replace slashes with dots and append a dot at the end if there is any content in the package root
    path = os.path.normpath(path)
    split_path = path.split(os.sep)
    package_root = ".".join(split_path)
    if len(package_root) > 0:
        package_root += "."
    return package_root


def get_class_special_case_package(package: str, class_name: str) -> str:
    if package == "std_msgs":
        return "Ros" + class_name
    return class_name


def generate_java_code_from_spec(
    path: str, spec: JavaClassSpec, external_package: str, blacklist: List[str]
) -> Tuple[str, str]:
    """
    Generates Java code for a class based on a JavaClassSpec.

    :param path: The package path.
    :param spec: JavaClassSpec instance representing the class.
    :param external_package: External package for imports.
    :param blacklist: List of fields that should use the external package.
    :return: Tuple with the path to the generated class and the generated code.
    """
    package_name, class_name = spec.msg_type.split("/")
    project_package_root = get_package_root(path)
    class_name = get_class_special_case_package(package_name, class_name)

    arg_strings = []
    imports = set()

    # Initialize code snippets
    fields_code = ""
    args = ""
    arg_assignment = ""
    getters = ""
    setters = ""
    json_constructor = ""

    # Iterate through the fields of the JavaClassSpec
    for name, field in spec.fields.items():
        if field.msg_type in blacklist:
            package_root = external_package
        else:
            package_root = project_package_root

        # Generate code snippets based on the field type and size
        if type(field) == JavaMessageField:
            if field.size == -1:
                results = generate_code_from_field(imports, package_root, name, field)
            elif field.size == 0:
                results = generate_code_from_field_variable_list(
                    imports, package_root, name, field
                )
            else:
                results = generate_code_from_field_static_list(
                    imports, package_root, name, field
                )
        elif isinstance(field, JavaClassSpec):
            if field.size == -1:
                results = generate_code_from_spec_sub_msg(
                    imports, package_root, name, field
                )
            elif field.size == 0:
                results = generate_code_from_spec_variable_list(
                    imports, package_root, name, field
                )
            else:
                results = generate_code_from_spec_static_list(
                    imports, package_root, name, field
                )
        else:
            raise ValueError(f"Invalid object found in fields: {field}")

        # Append the generated code snippets to the corresponding variables
        fields_code += results.fields_code
        arg_strings.append(results.arg)
        arg_assignment += results.arg_assignment
        getters += results.getter
        setters += results.setter
        json_constructor += results.json_constructor

    # Generate code for constants
    constants_code = ""
    for name, value in spec.constants.items():
        java_type = PYTHON_TO_JAVA_PRIMITIVE_MAPPING[type(value)]
        constants_code += f"{INDENT}public static {java_type.value} {name} = {value};\n"

    # Join arguments and remove the last character from arg_assignment and json_constructor
    args = ", ".join(arg_strings)
    arg_assignment = arg_assignment[:-1]
    json_constructor = json_constructor[:-1]

    # Add required imports
    imports.add("import com.google.gson.JsonObject;")
    imports.add("import com.google.gson.annotations.Expose;")

    # Sort and convert imports to a string
    imports = sorted(list(imports))
    import_code = "\n".join(imports)

    # Generate the constructor with arguments if there are any
    if len(arg_strings) > 0:
        args_constructor = f"""
{INDENT}public {class_name}({args}) {{
{arg_assignment}
{INDENT}}}
"""
    else:
        args_constructor = ""

    # Generate the final Java code for the class
    code = f"""// Auto generated!! Do not modify.
package {project_package_root}{package_name};

{import_code}

public class {class_name} extends {external_package}RosMessage {{
{constants_code}
{fields_code}
    @Expose(serialize = false, deserialize = false)
    public final java.lang.String _type = "{spec.msg_type}";

    public {class_name}() {{

    }}
{args_constructor}
    public {class_name}(JsonObject jsonObj) {{
{json_constructor}
    }}

{getters}
{setters}
    public JsonObject toJSON() {{
        return ginst.toJsonTree(this).getAsJsonObject();
    }}

    public java.lang.String toString() {{
        return ginst.toJson(this);
    }}
}}
"""

    path = f"{package_name}/{class_name}.java"

    return path, code
