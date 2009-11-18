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

    #sort() doesn't handle upper and lower case comparisons properly.
    #The following manipulation will ensure the list is in the same
    #order 'ls' returns on a directory
    tmp = []
    for i, group in enumerate(ret):
        tmp.append([group.lower(), group])

    tmp.sort()
    ret = []
    for key, group in tmp:
        ret.append(group)

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

def get_subset_test_list(test_suite, test_subset):
    """Return a list of dictionaries for a specific set of groups.
       It will contain the group and test filename
    """
    ret = []
  
    str = test_subset.strip('[]')

    if test_subset.find(",") >= 0:
        groups = str.split(',')

    elif test_subset.find(":") >= 0:
        groups = str.split(':')
        if len(groups) != 2:
            return ret

        all_groups = list_groups(test_suite)
        index_start = all_groups.index(groups[0])
        index_end = all_groups.index(groups[1])

        if index_start < 0:
            print "Group %s (%d) was not found" % (groups[0], index_start)
            return ret
        elif index_end < 0:
            print "Group %s (%d) was not found" % (groups[1], index_end)
            return ret
        elif index_end < index_start:
            print "Group %s's index (%d) is < Group %s's index (%d)" % \
                   (groups[1], index_end, groups[0], index_start)
            return ret

        groups = all_groups[index_start:index_end + 1]

    else:
        return ret

    for group in groups:
        tmp = get_group_test_list(test_suite, group)
        ret = ret + tmp

    return ret

