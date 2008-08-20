#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Jay Gagnon <jay.gagnon@gmail.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Murillo F. Bernardes <mfb@br.ibm.com>
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
from xmlrpclib import ServerProxy, Error

DEFAULT_RPC_URL = "http://morbo.linux.ibm.com/xenotest/testrun/api"

DEFAULT_LOG_FILE = "run_report.txt"

import Reporter
import re 
import os
from CimTest.ReturnCodes import PASS, FAIL, XFAIL, SKIP

class TestSuite:
    """Test Suite class to make the output of driving test suites a bit more consistant"""

    def __init__(self, log=False, file_name=None):
        if log == True:
            if file_name is None:
                self.log_file = DEFAULT_LOG_FILE
            else:
                self.log_file = file_name

            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            self.log_fd = open(self.log_file, "w")
        else:
            self.log_file = None
            self.log_fd = None

        self.rep = Reporter.Reporter(verbosity=5, log_fd=self.log_fd)

    def print_results(self, group, test, status, output=""):
        bug = None
        if status == XFAIL:
            err = "Test error: returned XFAIL without a valid bug string."
            bug = err
            if len(output) > 0:
                try:
                    str = re.search('Bug:<[0-9]*>', output).group()
                    bug = re.search("Bug:<([0-9]+)>", str).group(1)
                    if len(str) > 0:
                        if output == str:
                            #No need to pring bug twice
                            output = ""
                except:
                    #If we hit a problem, make sure bug = error msg
                    bug = err

        self.rep.results("%s - %s" % (group, test), status, bug)
        if output and status != PASS:
            self.rep.debug(1, output)

    def debug(self, str):
            self.rep.debug(1, str)
 
    def finish(self):
        if self.log_fd is not None:
            self.log_fd.close()

class RPCTestSuite:
    """Test Suite class to make the output of driving test suites a bit more consistant

    RPC version. It will register the test results on the server
    """

    def __init__(self, name, buildid, machine, rpc_url = DEFAULT_RPC_URL):
        self.server = ServerProxy(rpc_url)
        self.testid = self.server.RegisterTest(name, buildid, machine)

    def ok(self, group, test, output=""):
        self.server.RegisterPass(self.testid, group, test)
        print "%s - %s:\tPASS" % (group, test)

    def skip(self, group, test, output=""):
        self.server.RegisterSkip(self.testid, group, test)
        print "%s - %s:\tSKIP" % (group, test)
        if output:
            print output

    def fail(self, group, test, output=""):
        self.server.RegisterFail(self.testid, group, test, output)
        print "%s - %s:\tFAIL" % (group, test)
        if output:
            print output
        
    def xfail(self, group, test, output=""):
        self.server.RegisterXfail(self.testid, group, test, output)
        print "%s - %s:\tXFAIL" % (group, test)
        if output:
            print output

    def finish(self):
        self.server.FinishTest(self.testid)
    
