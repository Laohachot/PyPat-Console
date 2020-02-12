'''
Mock file 
'''

import inspect
from types import FunctionType
import numpy as np
from shlex import split, quote

def wrappy(func):
    def wrap(*args, **kwargs):
        return func(*args, **kwargs)
    wrap.__wrapped__ = func
    return wrap

@wrappy
def a(lol: str, x: int, y: float, z: list, i: dict, j: tuple):
    print(locals())


input_string = '"cat and dog" 1 2 [1,2,3] \{1:1,2:2\} (1,2,3)'

# Enforce type hints

def handle_string_of_args(func, argstring):
    argsspec = inspect.getfullargspec(inspect.unwrap(func))
    args = argsspec.args
    argtypes = argsspec.annotations

    n_args = len(args)
    n_typed = len(argtypes)

    special_cases = {tuple:eval, list:eval, dict:eval}

    print(split(argstring))

    # TODO: Handle lists, tuples, dicts of strings
    arglist = [] 
    for arg, type_ in zip(split(argstring), argtypes.values()):
        if type_ in special_cases:
            arglist.append(special_cases[type_](arg))
        else:
            arglist.append(type_(arg))
        
    print(arglist)
    a(*arglist)


handle_string_of_args(a, input_string)


