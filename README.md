# Generic-Configuration-Builder
 A simple library for parsing a configuration file format which is intended to build dependencies and hold parameters - well suited for experimentation settings in which different experiments use different clases.

## Installation

## Syntax
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
Optionally at the end of the configuration you may define a `~RETURN` section which specifies which instances will be returned by the `.build()` function of the `GenericConfigurationBuilder`


## Examples
