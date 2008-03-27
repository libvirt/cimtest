#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Jay Gagnon <jay.gagnon@gmail.com>
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
class Reporter:

    def __init__(self, verbosity=1):
        self.verbosity = verbosity

    def __red(self, str):
        return "\033[01;31m%s\033[00m" % str

    def __yellow(self, str):
        return "\033[01;33m%s\033[00m" % str
        
    def __green(self, str):
        return "\033[01;32m%s\033[00m" % str
        
    def __blue(self, str):
        return "\033[01;34m%s\033[00m" % str
        
    def __out(self, str):
        """We might not always be just printing output to stdout, so this should
        be used for all output."""
        # Right now we just mimic print.
        print(str)
    
    def debug(self, level, str):
        """Produces debug output if appropriate for current verbosity level.
        
        level: Debug priority of output.  1 is highest, 5 is lowest.  Higher
        priority output will be printed in the most levels, while low priority
        output will only be printed when verbosity is high."""
        if level <= self.verbosity:
            self.__out(str)

    def pass_test(self, test_name):
        str = self.__green("PASS")
        self.__out("%s: %s" % (test_name, str))

    def fail_test(self, test_name):
        str = self.__red("FAIL")
        self.__out("%s: %s" % (test_name, str))

    def xfail_test(self, test_name, bug):
        str = self.__blue("XFAIL")
        self.__out("%s: %s\tBug: %s" % (test_name, str, bug))

    def skip_test(self, test_name):
        str = self.__yellow("SKIP")
        self.__out("%s: %s" % (test_name, str))
