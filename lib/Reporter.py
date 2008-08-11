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
from CimTest.ReturnCodes import PASS, FAIL, SKIP, XFAIL

class Reporter:

    def __init__(self, verbosity=1, log_fd=None):
        self.verbosity = verbosity
        self.log_fd = log_fd

    def __red(self, str):
        return "\033[01;31m%s\033[00m" % str

    def __yellow(self, str):
        return "\033[01;33m%s\033[00m" % str
        
    def __green(self, str):
        return "\033[01;32m%s\033[00m" % str
        
    def __blue(self, str):
        return "\033[01;34m%s\033[00m" % str
        
    def __out(self, str, status, bug):
        def no_color(string):
            return string

        colors = { "FAIL"  : self.__red,
                   "PASS"  : self.__green,
                   "SKIP"  : self.__yellow,
                   "XFAIL" : self.__blue,
                 }

        fn = colors.get(status, no_color)

        if status == XFAIL:
            print "%s: %s\tBug: %s" % (str, fn(status), bug)
        else:
            print "%s: %s" % (str, fn(status))

        if self.log_fd is not None:
            if status == XFAIL:
                self.log_fd.write("%s: %s\tBug: %s\n" % (str, status, bug))
            else:
                self.log_fd.write("%s: %s\n" % (str, status))
     
    def results(self, str, status, bug):

        rc = { FAIL  : "FAIL",
               PASS  : "PASS",
               SKIP  : "SKIP",
               XFAIL : "XFAIL"
             }
    
        self.__out(str, rc[status], bug) 
    
    def debug(self, level, str):
        """Produces debug output if appropriate for current verbosity level.
        
        level: Debug priority of output.  1 is highest, 5 is lowest.  Higher
        priority output will be printed in the most levels, while low priority
        output will only be printed when verbosity is high."""
        if level <= self.verbosity:
            print str
            self.log_fd.write("%s\n" % str)

