# Generic-Configuration-Builder
This library intends to help separate the setup and execution of experiments. If you need a bunch of different main classes to store the setup of your experiments, then this tiny library can help!
The library parses a file format that can be used to set up any kind of class dependencies including all parameters, while also leaving the option to input additional parameters into the setup.

## Installation
```
pip install generic_configuration_builder
```

## How to use
With a prepared configuration simply call:
```
from generic_configuration_builder import gcb_build

instances_dictionary = gcb_build("path/to/configuration.ini")
```

## Configuration Syntax
The .ini file format is used as follows:

```
[instance_name]
~Module = module_of.the_class
~Class = ClassName
constructor_argument_1 = 42
constructor_argument_2 = "int, strings, lists, dicts, tuples and None are supported"
constructor_argument_3 = [1,2,3,4]
constructor_argument_4 = (5,6,7,8)
constructor_argument_5 = {"key_1": "value_1",
                        "key_2": None}

[another_instance]
~MODULE = a_different.module
~CLASS = DifferentClass
argument_that_requieres_the_previous_class = *instance_name
more_arguments = ["a", 2]

[~RETURN]
RETURN = [instance_name, another_instance]
```

Each instance has a name that is given in brackets [].
After the name follows the module and the class name of the class that is supposed to be instantiated here, indicated by the keyword `~MODULE` and `~CLASS` keywords.
Then the arguments that will be passed to the constructor follow with the name of the argument leading, the equal sign and the value follow. The basic python built-in types are supported here. <br>
Previously defined instances can be used as arguments to other instances by using a * followed by a previously defined instance name.<br>
Optionally at the end of the configuration, you may define a `~RETURN` section which specifies which instances will be returned by the `.gcb_build()` function as a dictionary. In this dictionary the instance names are the keys and the initialized instances are the values. If this section is not defined only the last created instance in the configuration file is returned as a single object (not a dictionary).

## Other features

### Placeholder variables
If you don't want to fix all parameters in the configuration you can write placeholders in the same way as you do with previously defined instances.

```
[thingy]
~MODULE = module_of.thingy
~CLASS = ThingyClass
argument_i_dont_want_to_define_in_config = *name_of_argument
...
```
To fill `name_of_argument` with a value, pass a keyword argument with the same name to the `gcb_build()` function. For example:
```
from generic_configuration_builder import gcb_build

instances_dictionary = gcb_build("path/to/configuration.ini", 
                                    name_of_argument = 42)
```

Here there is no restriction on datatypes. You may pass any object like this.

### Default values for placeholders
If you only sometimes want to change a parameter but most of the time want to use a default value you can use default values defined in a `~DEFAULT` section as follows:

```
[~DEFAULT]
name_of_argument = "This is the default value for this argument."
funny_number = 24
...
```
The default value can be overwritten by passing an according keyword argument to the `gcb_build()` function as follows:
```
instances_dictionary = gcb_build("path/to/configuration.ini", name_of_argument="this_string_overwrites_the_default",
funny_number=25)
```

### Use child objects as arguments

If you want to pass the child object of some instance to another instance you can do it the same why as you would in python by using dots `.`
```
...

[foo]
~MODULE = foos.module
~CLASS = FooClass
argument_that_needs_chield_from previous_instance = *name_of_previous_instance.child
```

This works recursively, so you could write `*instance.child.subchild` as well.

### Using nested instances

You can nested an instance inside a list, tuple or dictionary and it will still be recognized. This also works recursively. For example like this:

```
[some_thing]
~MODULE = some
~CLASS = Thing
dict_with_instance = {"object": *this_is_an_instance, 
                    {"sub_dictionary_key": *this_is_another_instance}},
                    {*instance_as_key : "some value"}
list_of_tuple = [(*instance_1, *instance_2.child, 'a normal string'),
                 (*instance_3, None, 'another_string')]
```
Note that not all objects can be keys of dictionaries.

### Parsing torch and numpy arrays

If you have numpy or pytorch installed AND the class you want to instantiate uses type hints in the signature of its `__init__` function, then you may pass an array as arguments in addition to the other data types. The correct format here is the one you get when you `print()` the according array or tensor. These special data types can not be nested inside collections.

## Examples 
Specific examples without any other python packages are not very helpful as native python classes usually don't need this kind of construction. 
So here is a simple example with some made-up classes.
Assume the existence of `classes.py` in the working directory with the following content:
```
class ChildClass():
    def __init__(self, some_string: str, some_float: float, another_string: str) -> None:
        self.some_string = some_string
        self.some_float = some_float
        self.combined_string = some_string + str(some_float)
        self.another_string = another_string

class ParentClass():
    def __init__(self, some_int: int, combined_string: str) -> None:
        self.some_int = some_int
        self.combined_string = combined_string
```

An `example_config.ini` could look like this:
```
[~DEFAULT]
an_integer = 25

[child_instance]
~MODULE = classes
~CLASS = ChildClass
some_string = "blub"
some_float = 3.141
another_string = *another_string

[parent_instance]
~MODULE = classes
~CLASS = ParentClass
some_int = *an_integer
combined_string = *child_instance.combined_string

[~RETURN]
RETURN = [child_instance, parent_instance, parent_instance.combined_string]
```

Note that `another_string` is not defined in the config and therefore needs to be passed as an argument to `gcb_build()`. The argument `an_integer` has a default value and therefore can be passed optionally to the function as an argument.

This configuration could for example be built as follows:

```
from generic_configuration_builder import gcb_build

instances_dict = gcb_build("./example_config.ini", 
                           another_string = "this is not part ot the config")
```

After execution `instances_dict` contains a dictionary of the instance:
```
{
    'child_instance': <classes.ChildClass object at 0x7fd91416ea70>,
    'parent_instance': <classes.ParentClass object at 0x7fd91416ec50>,
    'parent_instance.combined_string': 'blub3.141'
}
```
Which now can be used in whatever way these objects are intended to be used.

Some extensive examples using a complex class structure can be found [here](https://github.com/Sebastian-Griesbach/Improving-Policy-Conditioned-Value-Functions/tree/main/experiments).
