#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
"""Some utilities to xenoblade test suite
"""

import os
import glob

# Group utils

def list_groups(test_suite):
    """Return all groups contained in test_suite.
    All directories inside test_suite are groups by definition
    """
    ret = []
    for filename in os.listdir(test_suite):
        group_p = os.path.join(test_suite, filename)
        if os.path.isdir(group_p):
            ret.append(filename)

    ret.sort()
    return ret

def list_tests_in_group(test_suite, group_name):
    """Return a sorted list of available tests in a group.
    All tests must have a filename matching [0-9][0-9]-*.py"""
    orig_dir = os.path.abspath(os.curdir)

    try:
        os.chdir("%s/%s/" % (test_suite, group_name))

    except Exception, details:
        return [] 

    two_digits = glob.glob("[0-9][0-9]_*.py")
    two_digits.sort()
    
    three_digits = glob.glob("[0-9][0-9][0-9]_*.py")
    three_digits.sort()

    ret = two_digits + three_digits
    os.chdir(orig_dir)
    return ret

def get_group_test_list(test_suite, group):
    """Return a list of dictionaries for a specific group.
       It will contain the group and test filename
    """
    ret = []

    for test in list_tests_in_group(test_suite, group):
        ret.append({ 'group': group, 'test': test})

    return ret

def list_all_tests(test_suite):
    """Return a list of dictionaries, containing the group and test filename
    """
    ret = []

    for group in list_groups(test_suite):
        for test in list_tests_in_group(test_suite, group):
            ret.append({ 'group': group, 'test': test})

    return ret

def get_one_test(test_suite, group, test):
    """Return a dictionary that contains the group and test filename
    """
    ret = []

    for item in list_tests_in_group(test_suite, group):
        if item == test:
            ret.append({ 'group': group, 'test': test})
            
    return ret
