#!/usr/bin/env python
"""
Created : 21-06-2018
Last Modified : Fri 22 Jun 2018 06:46:45 PM EDT
Created By : Enrique D. Angola
"""

import json
import os

import scipy.io as spio
import pandas as pd


def loadmat(filename):
    '''
    this function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    '''
    data = spio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)


def _check_keys(dict):
    '''
    checks if entries in dictionary are mat-objects. If yes
    todict is called to change them to nested dictionaries
    '''
    for key in dict:
        if isinstance(dict[key], spio.matlab.mio5_params.mat_struct):
            dict[key] = _todict(dict[key])
    return dict


def _todict(matobj):
    '''
    A recursive function which constructs from matobjects nested dictionaries
    '''
    dict = {}
    for strg in matobj._fieldnames:
        elem = matobj.__dict__[strg]
        if isinstance(elem, spio.matlab.mio5_params.mat_struct):
            dict[strg] = _todict(elem)
        else:
            dict[strg] = elem
    return dict


def mat2json(filename, savename):
    """
    Converts .mat file to .json and writes new file

    Parameters
    ----------
    filename: Str
        path/filename of .mat file
    savename: Str
        path to write converted file

    Returns
    -------
    None

    Examples
    --------
    >>> mat2json(blah blah)

    """

    matlabFile = loadmat(filename)
    # pop all those dumb fields that don't let you jsonize file
    matlabFile.pop('__header__')
    matlabFile.pop('__version__')
    matlabFile.pop('__globals__')
    # jsonize the file - orientation is 'index'
    matlabFile = pd.Series(matlabFile).to_json(indent=4)
    with open(savename, 'w') as f:
        f.write(matlabFile)
