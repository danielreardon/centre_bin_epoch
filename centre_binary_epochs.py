#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 15:15:31 2023

@author: dreardon
"""

import argparse
from decimal import Decimal, InvalidOperation


def read_par(parfile):
    """
    Reads a par file and returns a dictionary of parameter names and values, 
    the original lines, and the line number containing T0 or TASC.
    """
    par = {}
    ignore = ['DMMODEL', 'DMOFF', "DM_", "CM_", 'CONSTRAIN', 'JUMP', 'NITS',
              'NTOA', 'CORRECT_TROPOSPHERE', 'PLANET_SHAPIRO', 'DILATEFREQ',
              'TIMEEPH', 'MODE', 'TZRMJD', 'TZRSITE', 'TZRFRQ', 'EPHVER',
              'T2CMETHOD']
    original_lines = []
    t0_tasc_line_number = None
    line_number = 0

    with open(parfile, 'r') as file:
        for line in file:
            original_lines.append(line)
            sline = line.split()

            # Skip comments, empty lines, and ignored parameters
            if len(sline) == 0 or line[0] in "#C" or sline[0] in ignore:
                line_number += 1
                continue

            # Processing the parameter line
            param, val, err, p_type = process_param_line(sline)
        
            # Store the parameters and error if any
            par[param] = val
            if err:
                par[param+"_ERR"] = float(err)
            if p_type:
                par[param+"_TYPE"] = p_type

            # Check for T0/TASC line number
            if param in ['T0', 'TASC']:
                t0_tasc_line_number = line_number

            line_number += 1

    return par, original_lines, t0_tasc_line_number

def process_param_line(sline):
    """
    Processes a single line from the par file and returns the parameter,
    value, error, and type.
    """
    param = sline[0]
    if param == "E":
        param = "ECC"

    val_str = sline[1].replace('D', 'E')
    err = None
    p_type = None

    # Check if the value is numeric
    if is_numeric(val_str):
        try:
            # Convert to Decimal for high precision
            val = Decimal(val_str)
            p_type = 'd' if val_str.isdigit() else 'e'
        except InvalidOperation:
            # Fallback to string if Decimal conversion fails
            val = val_str
            p_type = 's'
    else:
        # Keep as string if it's not numeric
        val = val_str
        p_type = 's'

    # Handle errors if present
    if len(sline) >= 3 and sline[-1] not in ['0', '1']:
        try:
            err = Decimal(sline[-1].replace('D', 'E'))
        except InvalidOperation:
            err = None  # Ignore the error if conversion fails

    return param, val, err, p_type

def is_numeric(s):
    """
    Checks if the given string s represents a numeric value.
    """
    try:
        Decimal(s)
        return True
    except InvalidOperation:
        return False



def write_updated_par(par, original_lines, t0_tasc_line_number, new_parfile):
    """
    Writes an updated .par file with the new T0 or TASC value.
    """
    with open(new_parfile, 'w') as file:
        for i, line in enumerate(original_lines):
            if i == t0_tasc_line_number:
                param = 'T0' if 'T0' in par else 'TASC'
                file.write(f"{param} {par[param]} 1\n")
            else:
                file.write(line)

# Set up argparse for command-line arguments
parser = argparse.ArgumentParser(description='Centre the binary epoch of a .par file. Note: Does not handle binary derivatives. Please use pulse numbers and "TRACK -2" to refit after centring')
parser.add_argument('-i', '--input', required=True, help='Input .par file name')
parser.add_argument('-o', '--output', help='Output .par file name', default='updated.par')
parser.add_argument('-e', '--epoch', type=float, help='Target centre epoch (optional)')
args = parser.parse_args()

# Read parameters from the input .par file
pars, original_lines, t0_tasc_line_number = read_par(args.input)

# Calculate the target epoch
if args.epoch is not None:
    target_epoch = Decimal(args.epoch)
else:
    start = pars.get('START')
    finish = pars.get('FINISH')
    if start is None or finish is None:
        raise KeyError('Error: START and FINISH values must be present in .par file or set epoch on command line')
    target_epoch = (finish + start) / Decimal('2')

# Determine the reference epoch key (T0 or TASC) and calculate the updated value
epoch_key = 'T0' if 'T0' in pars else 'TASC'
try:
    pb = pars['PB']
except KeyError:
    pb = Decimal('1') / pars['FB0'] / Decimal('86400')  # Convert from frequency to days

# Calculate the number of orbits to advance
norbs = (target_epoch - pars[epoch_key]) // pb

# Update the epoch
pars[epoch_key] += norbs * pb

# Write the updated .par file
write_updated_par(pars, original_lines, t0_tasc_line_number, args.output)


