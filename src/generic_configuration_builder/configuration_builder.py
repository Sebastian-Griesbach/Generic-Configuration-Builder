import inspect
import configparser
from collections import OrderedDict
import os
import ast

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

MODULE_MARKER = "~MODULE"
CLASS_MARKER = "~CLASS"
VARIABLE_INDICATOR = "*"
RETURN_SECTION = "~RETURN"
RETURN_ATTRIBUTE = "RETURN"

def gcb_build(configuration_path, **input_instances):
    configuration = _read_configuration(configuration_path)

    variables_dict = OrderedDict(**input_instances)

    for section in configuration.sections():
        if(section == RETURN_SECTION):
            return_variable_names = _parse_unmarked_string_list(configuration[RETURN_SECTION][RETURN_ATTRIBUTE])
            return_dict = {}
            for variable_name in return_variable_names:
                attribute_parts=variable_name.split(".")
                base_instance = variables_dict[attribute_parts[0]]
                return_dict[attribute_parts[-1]] = _get_attribute(base_instance=base_instance, attribute_parts=attribute_parts[1:])
            return return_dict

        module_name = configuration[section].pop(MODULE_MARKER)
        class_name = configuration[section].pop(CLASS_MARKER)
        instance = initialize_class(module_name, class_name, configuration[section], variables_dict)
        variables_dict[section] = instance

    return variables_dict.popitem()[1]

def _read_configuration(configuration_path):
    absolut_configuration_path = os.path.abspath(configuration_path)
    configuration = configparser.ConfigParser()
    configuration.read(absolut_configuration_path)
    return configuration

def initialize_class(module_name, class_name, init_args_string_dict, variables_dict):
    _class = load_class(module_name, class_name)

    full_arg_spec = inspect.getfullargspec(_class.__init__)

    init_args = full_arg_spec.args
    if "self" in init_args: init_args.remove("self")
    init_args_types = dict.fromkeys(init_args)

    annotations_dict = full_arg_spec.annotations
    annotations_dict.pop("return", None)

    init_args_types.update(annotations_dict)

    init_args_instances = {}
    for arg_name, arg_string in init_args_string_dict.items():
        if(arg_string.startswith(VARIABLE_INDICATOR)):
            attribute_name = arg_string[len(VARIABLE_INDICATOR):]
            attribute_parts = attribute_name.split(".")
            base_instance = variables_dict[attribute_parts[0]]
            instance = _get_attribute(base_instance, attribute_parts[1:])
            init_args_instances[arg_name] = instance
            continue
        
        if arg_name in init_args_types:
            init_args_instances[arg_name] = _parse_value(dtype=init_args_types[arg_name],string=arg_string)
        elif full_arg_spec.varkw != None:
            init_args_instances[arg_name] = ast.literal_eval(arg_string)

    return _class(**init_args_instances)

def load_class(module_name, class_name):
    module = __import__(module_name, fromlist=class_name)
    _class = getattr(module, class_name)
    return _class

def _get_attribute(base_instance, attribute_parts):
    instance = base_instance
    for attribute_name in attribute_parts:
        instance = getattr(instance, attribute_name)

    return instance

def _parse_value(dtype, string):
    try:
        parsed = _parse_function_of(dtype)(string)
    except Exception as error:
        raise Exception(f"Error while trying to parse: {string} as: {dtype}").with_traceback(error.__traceback__)

    return parsed

def _parse_function_of(dtype):
    if( HAS_TORCH and dtype == torch.Tensor):
        return _parse_torch_tensor
    if( HAS_NUMPY and dtype == np.ndarray):
        return _parse_numpy_array

    return ast.literal_eval


### Special parse functions

def _parse_unmarked_string_list(list_string):
    list_string = list_string[1:-1].split(",")
    list_string = list(map(lambda item: item.strip(" "), list_string))
    return list_string

def _parse_torch_tensor(tensor_string):
    if(tensor_string.startswith("tensor")):
        tensor_string = tensor_string[7:-1]

    parsed_list = ast.literal_eval(tensor_string)
    tensor = torch.tensor(parsed_list, dtype=torch.float32)
    return tensor

def _parse_numpy_array(array_string):
    if(array_string.startswith("array")):
        tensor_string = array_string[6:-1]

    parsed_list = ast.literal_eval(tensor_string)
    array = np.array(parsed_list, dtype=np.float32)
    return array


    