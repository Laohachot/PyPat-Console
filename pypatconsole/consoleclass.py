'''
Contains the command line interface (CLI) class, along its factory function:
menu()
'''

from time import sleep
import pypatconsole.consolestrings as strings
import pypatconsole.consoleconfig as ccng 
from pypatconsole.funcmap import (construct_funcmap, print_funcmap, 
                                 _docstring_firstline)
from pypatconsole.consolecommon import (clear_screen, input_splitter, 
                                        list_local_cases, print_help)
from typing import Union, Callable
from inspect import getfullargspec, unwrap, signature
from types import ModuleType

def logo_title(title: str):
    '''Prints logo title'''
    print("{:-^40s}".format(title))

def show_cases(funcmap: dict, title=strings.LOGO_TITLE):
    '''Prints function map prettily with a given title'''
    logo_title(title)
    print_funcmap(funcmap)

def enter_prompt(msg: str=strings.ENTER_PROMPT):
    '''Prints enter prompt message and than returns input()'''
    print(msg, end=': ')
    return input()

def exit_program(*args, **kwargs):
    '''
    Exit program
    '''
    print(strings.EXIT_MSG)
    sleep(ccng.MSG_WAIT_TIME)
    clear_screen()
    exit()

__SPECIAL_ARG_CASES = {
    str: lambda x: str(x.strip("\"\'")), # Removes outer " or ' characters
    tuple:eval, 
    list:eval, 
    dict:eval,
    set:eval
}

def _handle_arglist(func, arglist):
    '''
    Handles list of strings that are the arguments 
    The function turns the strings from the list into 
    their designated types (found from function signature).
    '''
    argsspec = getfullargspec(unwrap(func))
    args = argsspec.args
    argtypes = argsspec.annotations

    if len(arglist) > len(args):
        raise TypeError(f'Got too many arguments, should be {len(args)}, but got {len(arglist)}')

    # Special proceedures for special classes
    typed_arglist = [] 
    for arg, type_ in zip(arglist, argtypes.values()):
        if type_ in __SPECIAL_ARG_CASES:
            typed_arglist.append(__SPECIAL_ARG_CASES[type_](arg))
        else:
            typed_arglist.append(type_(arg))

    return typed_arglist

def _error_info(error, func):
    print(strings.ERROR_INDICATOR)
    print(f'Selected case: "{_docstring_firstline(func)}"')
    print(error)
    print(f'Function signature: {signature(func)}')
    print()
    print(strings.INPUT_WAIT_PROMPT_MSG)
    input()

class CLI:
    '''
    Command Line Interface class 
    '''
    def __init__(self, cases, title: str=strings.LOGO_TITLE, 
                 blank_proceedure: Union[str, Callable]='return', 
                 decorator: Callable=None):
        '''
        Input
        -----
        cases: 

        if given a module: module containing functions that serves as cases a 
        user can pick from terminal interface. the module should not implement
        any other functions. 
        
        if given a list: will simply use function in list as cases.

        First line of docstring becomes case description
        ALL CASES MUST CONTAIN DOCSTRINGS

        title: String to print over alternatives 

        blank_proceedure: What to do when given blank input (defaults to 
                          stopping current view (without exiting))
        '''
        self.funcmap = construct_funcmap(cases, decorator=decorator)
        self.title = title

        if blank_proceedure == 'return':
            self.blank_hint = strings.INPUT_BLANK_HINT_RETURN
            self.blank_proceedure = self.__return_to_parent
        elif blank_proceedure is 'pass':
            self.blank_hint = strings.INPUT_BLANK_HINT_PASS
            self.blank_proceedure = self.__pass
        elif blank_proceedure == 'exit':
            self.blank_hint = strings.INPUT_BLANK_EXIT
            self.blank_proceedure = exit_program
        else:
            self.blank_proceedure = blank_proceedure

        # Special options
        self.special_cases = {
            '..':self.__return_to_parent,
            'q':exit_program,
            'h':print_help
        }

    def __return_to_parent(self):
        self.active = False
    
    def __pass(self):
        pass

    def _handle_case(self, casefunc, inputlist):
        try:
            if inputlist:
                # Raises TypeError if wrong number of arguments 
                casefunc(*_handle_arglist(casefunc, inputlist))
            else:
                # Will raise TypeError if casefunc() actually 
                # requires arguments
                casefunc()
        except TypeError as e:
            _error_info(e, casefunc)

    def run(self):
        '''
        Main function for console interface
        '''
        self.active = True
        try:
            while self.active:
                clear_screen()
                show_cases(self.funcmap, self.title)

                # Get key to func map
                print()
                print(self.blank_hint)
                inputstring = enter_prompt(strings.ENTER_PROMPT)

                # Pressing enter without specifying enables if test
                clear_screen()
                if not inputstring:
                    self.blank_proceedure()
                    continue

                # Tokenize input
                inputlist = input_splitter(inputstring)
                # Get case
                case = inputlist.pop(0)

                if case in self.funcmap:
                    # Obtain case function from funcmap and 
                    # calls said function. Recall that items are 
                    # (description, function), hence the [1]
                    casefunc = self.funcmap[case][1]
                    self._handle_case(casefunc, inputlist)
                elif case in self.special_cases:
                    # Items in special_cases are not tuples, but the 
                    # actual functions, so no need to do [1]
                    casefunc = self.special_cases[case]
                    self._handle_case(casefunc, inputlist)
                else:
                    print(strings.INVALID_TERMINAL_INPUT_MSG)
                    sleep(ccng.MSG_WAIT_TIME)

        except KeyboardInterrupt:
            # Ensures proper exit when Kbinterrupt
            exit_program()
    
def menu(cases: Union[list, dict, ModuleType], title: str=' Title ', 
                blank_proceedure: Union[str, Callable]='return', 
                decorator: Callable=None, run: bool=True, main: bool=False):
    '''
    Factory function for the CLI class. This function initializes a menu. 

    Parameters
    ------------
    cases: Can be output of locals() (a dictionary) from the scope of the cases 
           
           Or a list functions 

           Or a module containing the case functions

    title: title of menu

    blank_proceedure: What to do the when given blank input. Can be user defined
                      function, or it can be a string. Available string options
                      are:
                      
                      'return', will return to parent menu, if you are at main
                      menu, this will exit the program

                      'pass', does nothing. This should only be used for the 
                      main menu

                      'exit', exits the program

    decorator: Decorator for case functions

    run: To invoke .run() method on CLI object or not.

    Returns
    --------
    CLI (Command Line Interface) object. Use .run() method to activate menu. 
    '''
    if type(cases) == list:
        cases_to_send = cases
    elif type(cases) == dict:
        cases_to_send = list_local_cases(cases)
        # If this menu is the first menu initialized, and is given the locally
        # defined functions, then must filter the functions that are defined 
        # in __main__
        if main:
            cases_to_send =\
                [c for c in cases_to_send if c.__module__ == '__main__']
            blank_proceedure='pass'

    elif type(cases) == ModuleType:
        cases_to_send = cases
    else:
        raise TypeError('Invalid type')

    cli = CLI(cases=cases_to_send, title=title, 
              blank_proceedure=blank_proceedure, decorator=decorator)
    if run:
        cli.run()
    
    return cli