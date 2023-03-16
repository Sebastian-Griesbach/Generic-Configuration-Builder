import inspect
import configparser
from collections import OrderedDict
import os
import ast
from typing import Union, Dict, Callable

### Optional Imports

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

### Keywords

MODULE_MARKER = "~MODULE"
CLASS_MARKER = "~CLASS"
INSTANCE_INDICATOR = "*"
RETURN_SECTION = "~RETURN"
RETURN_ATTRIBUTE = "RETURN"

### Code

def gcb_build(configuration_path: str, **input_instances) -> Union[Dict[str, object], object]:
    """ Build class and dependencies construct according to configuration file.

    Args:
        configuration_path (str): Path to configuration file

    Raises:
        Exception: Module keyword is missing in the config
        Exception: Class keyword is missing in the config
        Exception: Class instance could not be initialized due to another error.

    Returns:
        Union[Dict[str, object], object]: Dictionary of initialized classes or single object if the Return section is not specified in the config.
    """
    configuration = _read_configuration(configuration_path)

    variables_dict = OrderedDict(**input_instances)

    for section in configuration.sections():
        if(section == RETURN_SECTION):
            return_variable_names = _parse_unmarked_string_list(configuration[RETURN_SECTION][RETURN_ATTRIBUTE])
            return_dict = {}
            for variable_name in return_variable_names:
                return_dict[variable_name] = _get_attribute(argument_string=variable_name, variables_dict=variables_dict)
            return return_dict

        try:
            module_name = configuration[section].pop(MODULE_MARKER)
        except KeyError as key_error:
            raise Exception(f'Instance "{section}" is missing the "{MODULE_MARKER}" keyword') from key_error
        
        try:
            class_name = configuration[section].pop(CLASS_MARKER)
        except KeyError as key_error:
            raise Exception(f'Instance "{section}" is missing the "{CLASS_MARKER}" keyword') from key_error
        
        try:
            instance = _initialize_class(module_name, class_name, configuration[section], variables_dict)
        except Exception as exception:
            raise Exception(f'An error occurred while trying to initialize "{section}".') from exception
        variables_dict[section] = instance

    return variables_dict.popitem()[1]

def _read_configuration(configuration_path: str) -> list[str]:
    """Read the ini configuration given the path.

    Args:
        configuration_path (str): Path to the configuration

    Raises:
        Exception: The file could not be found.

    Returns:
        list[str]: The parsed ini config.
    """
    absolute_configuration_path = os.path.abspath(configuration_path)
    if not os.path.isfile(absolute_configuration_path):
        raise Exception(f'Configuration: {absolute_configuration_path} was not found.')
    configuration = configparser.ConfigParser()
    configuration.read(absolute_configuration_path)
    return configuration

def _initialize_class(module_name: str, class_name: str, init_args_string_dict: Dict[str, str], variables_dict: Dict[str, object]) -> object:
    """initialized a class given all information as strings

    Args:
        module_name (str): String that leads to the module of the class
        class_name (str): Name of the class
        init_args_string_dict (Dict[str, str]): Arguments of the __init__ function as strings with their according keywords.
        variables_dict (Dict[str, object]): A dictionary of already initialized classes. These could be used as arguments.

    Returns:
        object: Initialized instance of class.
    """
    _class = _load_class(module_name, class_name)

    full_arg_spec = inspect.getfullargspec(_class.__init__)

    init_args = full_arg_spec.args
    if "self" in init_args: init_args.remove("self")
    init_args_types = dict.fromkeys(init_args)

    annotations_dict = full_arg_spec.annotations
    annotations_dict.pop("return", None)

    init_args_types.update(annotations_dict)

    init_args_instances = {}
    for arg_name, arg_string in init_args_string_dict.items():
        if(arg_string.startswith(INSTANCE_INDICATOR)):
            instance = _get_attribute(argument_string=arg_string[len(INSTANCE_INDICATOR):], variables_dict=variables_dict)
            init_args_instances[arg_name] = instance
            continue
        
        if arg_name in init_args_types:
            init_args_instances[arg_name] = _parse_value(dtype=init_args_types[arg_name],string=arg_string)
        elif full_arg_spec.varkw != None:
            init_args_instances[arg_name] = ast.literal_eval(arg_string)

    return _class(**init_args_instances)

def _load_class(module_name: str, class_name: str) -> type:
    """Loads a class type given its location by strings.

    Args:
        module_name (str): String that leads to the module of the class
        class_name (str): Name of the class

    Returns:
        type: According python class type object
    """
    module = __import__(module_name, fromlist=class_name)
    _class = getattr(module, class_name)
    return _class

def _get_attribute(argument_string: str, variables_dict: Dict[str, object]) -> object:
    """Gets an attribute of an instance.

    Args:
        argument_string (str): String that describes path to the Attribute. E.g. "parent.child.subchild"
        variables_dict (Dict[str, object]): A dictionary of already initialized classes. This is where the attributes are in.

    Raises:
        Exception: When trying to extract an string that has not yet been associated to an object.

    Returns:
        object: Python object of the attribute
    """
    argument_attributes = argument_string.split(".")
    try:
        base_instance = variables_dict[argument_attributes[0]]
    except KeyError as key_error:
        raise Exception(f'"{argument_attributes[0]}" has not been assigned a value yet.') from key_error
    instance = base_instance
    for attribute_name in argument_attributes[1:]:
        instance = getattr(instance, attribute_name)

    return instance

def _parse_value(dtype: type, string: str) -> object:
    """Parse Python base datatypes from a string.

    Args:
        dtype (type): type to cast to.
        string (str): String to cast.

    Raises:
        Exception: When string could not be cast into desired into a datatype. Function no necessarily tries to parse to type dtype.

    Returns:
        object: Parsed string as Python object
    """
    try:
        parsed = _parse_function_of(dtype)(string)
    except Exception as error:
        raise Exception(f"Error while trying to parse: {string} as: {dtype}").with_traceback(error.__traceback__)

    return parsed

def _parse_function_of(dtype: type) -> Callable:
    """Returns function to parse a string to dtype.
        Always returns ast.literal_eval if dtype is not torch.Tensor or np.ndarray.

    Args:
        dtype (type): Type for which the parse function is needed.

    Returns:
        Callable: According parse function
    """
    if( HAS_TORCH and dtype == torch.Tensor):
        return _parse_torch_tensor
    if( HAS_NUMPY and dtype == np.ndarray):
        return _parse_numpy_array

    return ast.literal_eval

### Special parse functions

def _parse_unmarked_string_list(list_string: str) -> list[str]:
    """ Converts a string that represents a list without INSTANCE_INDICATOR to a list of strings. Each entry is assumed to be a variable.

    Args:
        list_string (str): String that represents a list.

    Returns:
        list[str]: List of strings where each string represents an instance.
    """
    list_string = list_string[1:-1].split(",")
    list_string = list(map(lambda item: item.strip(" "), list_string))
    return list_string

def _parse_torch_tensor(tensor_string: str) -> object:
    """Parses a string to a torch tensor.

    Args:
        tensor_string (str): String to parse

    Returns:
        torch.Tensor: Parsed tensor
    """
    if(tensor_string.startswith("tensor")):
        tensor_string = tensor_string[7:-1]

    parsed_list = ast.literal_eval(tensor_string)
    tensor = torch.tensor(parsed_list, dtype=torch.float32)
    return tensor

def _parse_numpy_array(array_string: str) -> object:
    """Parses a string to a numpy array.

    Args:
        array_string (str): String to parse

    Returns:
        np.ndarray: Parsed array
    """
    if(array_string.startswith("array")):
        tensor_string = array_string[6:-1]

    parsed_list = ast.literal_eval(tensor_string)
    array = np.array(parsed_list, dtype=np.float32)
    return array


    