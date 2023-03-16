# Generic-Configuration-Builder
 A simple library for parsing a configuration file format which is intended to build dependencies and hold parameters - well suited for experimentation settings in which different experiments use different class constructs. This can hide away the mess of different setups in a main class especially when the resulting interfaces are handled the same. These setups can be fully described with these configuration files.

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
constructor_argument_2 = "int, strings, lists, dicts and tuples are supported"
constructor_argument_3 = [1,2,3,4]
constructor_argument_4 = (5,6,7,8)
constructor_argument_5 = {"key_1": "value_1",
                        "key_2": "value_2"}

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
Then the arguments that will be passed to the constructor follow with the name of the argument leading the equal sign and the value following. The basic python buildin types are supported here. <br>
Previously defined instances can be used as arguments to other instances by using a * followed by previously defined instance name.<br>
Optionally at the end of the configuration you may define a `~RETURN` section which specifies which instances will be returned by the `.gcb_build()` function as a dictionary with their instance names as keys and the instances as values. If this section is not defined only the last created instance in the config is returned as a single object.

## Other features

### Placeholder variables
If you don't want to fix all parameters in the configuration you can write placeholders in the same way as you use previously defined instances.

```
[thingy]
~MODULE = module_of.thingy
~CLASS = ThingyClass
argument_i_dont_want_to_define_in_config = *name_of_argument
...
```
The fill `name_of_argument` with a value pass a keyword argument with the same name to the `gcb_build()` function.

```
from generic_configuration_builder import gcb_build

instances_dictionary = gcb_build("path/to/configuration.ini", 
                                    name_of_argument = 42)
```

Here there is no restriction on datatypes. You may pass any object like this.

### Use child objects as arguments

If you want to pass the child object of some instance to another instance you can do it the same why as you would in python by using dots `.`
```
...

[foo]
~MODULE = foos.module
~CLASS = FooClass
argument_that_needs_chield_from previous_instance = *name_of_previous_instance.child

...
```

This works recursivly, so you could write `*instance.child.subchild` as well.

### Parsing torch and numpy arrays

If you have numpy or pytorch installed AND the class you want to instanciate uses type hints in the signature of its `__init__` function, then you may pass array as arguments additionally to the other data types.

## Examples 
Specific examples without any other python packages are not very helpful as native python classes usually don't need this kind of construction. 
So here is a simple example with some made up classes.
Assume the existance of `classes.py` in the working directory with the following content:
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
[child_instance]
~MODULE = classes
~CLASS = ChildClass
some_string = "blub"
some_float = 3.141
another_string = *another_string

[parent_instance]
~MODULE = classes
~CLASS = ParentClass
some_int = 25
combined_string = *child_instance.combined_string

[~RETURN]
RETURN = [child_instance, parent_instance, parent_instance.combined_string]
```

Note that `another_string` is not defined in the config and therefor needs to be passed as an argument to `gcb_build()`.

This configuration would be build as follows:

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
Which now can be used in whatever why these objects are intended to be used.

Some extensive examples using a complex class structure can be found [here](https://github.com/Sebastian-Griesbach/Improving-Policy-Conditioned-Value-Functions/tree/main/experiments).
