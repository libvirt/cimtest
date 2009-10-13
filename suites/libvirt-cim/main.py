#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Zhengang Li <lizg@cn.ibm.com>
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

from time import time
from optparse import OptionParser
import os
import sys
sys.path.append('../../lib')
import TestSuite
from CimTest.Globals import logger, log_param
import commands
from VirtLib import groups
import ConfigParser
sys.path.append('./lib')
from XenKvmLib.const import platform_sup, default_network_name, \
                            default_pool_name
from XenKvmLib.reporting import gen_report, send_report 
from VirtLib import utils
from XenKvmLib.xm_virt_util import virt2uri
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import create_netpool_conf, destroy_netpool, \
                                  create_diskpool_conf, destroy_diskpool, \
                                  pre_check

parser = OptionParser()
parser.add_option("-i", "--ip", dest="ip", default="localhost",
                  help="IP address of machine to test (default: localhost)")
parser.add_option("-m", "--target_url", dest="t_url", default="localhost:5988",
                  help="URL of destination host for remote migration ")
parser.add_option("-p", "--port", dest="port", type="int", default=5988,
                  help="CIMOM port (default: 5988)")
parser.add_option("-g", "--group", dest="group",
                  help="Specific test group (default: None)")
parser.add_option("-t", "--test", dest="test",
                  help="Specific test case (default: None).  \
Must specify --group or -g to use this option")
parser.add_option("-c", "--clean-log",  
                  action="store_true", dest="clean",
                  help="Will remove existing log files before test run")
parser.add_option("-v", "--virt", dest="virt", type="choice",
                  choices=['Xen', 'KVM', 'XenFV', 'LXC'], default="Xen",
                  help="Virt type, select from 'Xen' & 'KVM' & 'XenFV' & 'LXC'(default: Xen). ")
parser.add_option("-d", "--debug-output", action="store_true", dest="debug",
                  help="Duplicate the output to stderr")
parser.add_option("--report", dest="report",
                  help="Send report using mail info: --report=<recipient addr>")
parser.add_option("--print-exec-time", action="store_true", 
                  dest="print_exec_time",
                  help="Print execution time of each test")

TEST_SUITE = 'cimtest'
CIMTEST_RCFILE = '%s/.cimtestrc' % os.environ['HOME']

def set_python_path():
    previous_pypath = os.environ.get('PYTHONPATH')

    new_path = ['./lib', '../../lib']
    # make it abs path    
    new_path = map(os.path.abspath, new_path)

    if previous_pypath:
        new_path.append(previous_pypath)

    os.environ['PYTHONPATH'] = ":".join(new_path)

def remove_old_logs(ogroup):
    if ogroup == None:
        group_list = groups.list_groups(TEST_SUITE)
    else:
        group_list = [ogroup]

    for group in group_list:
        g_path = os.path.join(TEST_SUITE, group)
        cmd = "cd %s && rm -f %s" % (g_path, "cimtest.log")
        status, output = commands.getstatusoutput(cmd)

    print "Cleaned log files."


def get_rcfile_vals():
    if not os.access(CIMTEST_RCFILE, os.R_OK):
        print "\nCould not access the %s file for this user." % CIMTEST_RCFILE
        print "Create this file and add the appropriate relay:"
        print "\tfrom = me@isp.com\n\trelay = my.relay\n"
        return None, None

    try:
        conf = ConfigParser.ConfigParser()
        if not conf.read(CIMTEST_RCFILE):
            return None, None

        addr = conf.get("email", "from")
        relay = conf.get("email", "relay")

    except Exception, details:
        print "\n%s" % details 
        print "\nPlease verify the format of the %s file\n" % CIMTEST_RCFILE 
        return None, None

    return addr, relay

def setup_env(ip, virt):
    status, netpool = create_netpool_conf(ip, virt, 
                                          net_name=default_network_name)
    if status != PASS:
        print "\nUnable to create network pool %s" % default_network_name
        return status

    status, dpool = create_diskpool_conf(ip, virt, dpool=default_pool_name)
    if status != PASS:
        print "\nUnable to create disk pool %s" % default_pool_name
        status = destroy_netpool(ip, virt, default_network_name)
        if status != PASS:
            print "\nUnable to destroy network pool %s." % default_network_name 
        return FAIL

    return PASS

def cleanup_env(ip, virt):
    status = destroy_netpool(ip, virt, default_network_name) 
    if status != PASS:
        print "Unable to destroy network pool %s." % default_network_name
        return status

    status = destroy_diskpool(ip, virt, default_pool_name)
    if status != PASS:
        print "Unable to destroy disk pool %s." % default_pool_name
        return status

    return PASS

def print_exec_time(testsuite, exec_time, prefix=None):

    #Convert run time from seconds to hours
    tmp = exec_time / (60 * 60)
    h = int(tmp)

    #Subtract out hours and convert remainder to minutes
    tmp = (tmp - h) * 60 
    m = int(tmp)

    #Subtract out minutes and convert remainder to seconds
    tmp = (tmp - m) * 60 
    s = int(tmp)

    #Subtract out seconds and convert remainder to milliseconds
    tmp = (tmp - s) * 1000
    msec = int(tmp)

    if prefix is None:
        prefix = " "

    testsuite.debug("%s %sh | %smin | %ssec | %smsec" %
                    (prefix, h, m, s, msec)) 

def main():
    (options, args) = parser.parse_args()
    to_addr = None
    from_addr = None
    relay = None
    div = "--------------------------------------------------------------------"

    if options.test and not options.group:
        parser.print_help()
        return 1

    env_ready = pre_check(options.ip, options.virt)
    if env_ready != None: 
        print "\n%s.  Please check your environment.\n" % env_ready
        return 1

    # HACK: Exporting CIMOM_PORT as an env var, to be able to test things 
    # with a different port 
    if options.port:
        os.environ['CIMOM_PORT'] = str(options.port)
   
    # src and target host info to be able to use
    # in the tc for comparison in remote migration case
    if ":" in options.ip:
        (options.ip, port) = options.ip.split(":")

    if ":" in options.t_url:
        (options.t_url, port) = options.t_url.split(":")

    if options.report:
        to_addr = options.report
        from_addr, relay = get_rcfile_vals()
        if from_addr == None or relay == None:
            return 1
         
    testsuite = TestSuite.TestSuite(log=True)
    log_param(file_name=testsuite.log_file)
   
    set_python_path()

    if options.group and options.test:
        test_list = groups.get_one_test(TEST_SUITE, options.group, options.test)
    elif options.group and not options.test:
        test_list = groups.get_group_test_list(TEST_SUITE, options.group)
    else:
        test_list = groups.list_all_tests(TEST_SUITE)

    if not test_list:
        print "Test %s:%s not found" % (options.group, options.test)
        return 1

    if options.clean:
        remove_old_logs(options.group)

    if options.debug:
        dbg = "-d"
    else:
        dbg = ""

    status = setup_env(options.ip, options.virt)
    if status != PASS:
        print "Please check your environment.\n"
        testsuite.finish()
        return 1

    print "\nTesting " + options.virt + " hypervisor"

    test_run_time_total = 0

    for test in test_list: 
        testsuite.debug(div) 
        t_path = os.path.join(TEST_SUITE, test['group'])
        os.environ['CIM_TC'] = test['test'] 
        cdto = 'cd %s' % t_path
        run = 'python %s -i %s -v %s %s -m %s' % (test['test'], options.ip, 
                                                  options.virt, dbg,
                                                  options.t_url)
        cmd = cdto + ' && ' + ' ' + run
        start_time = time()
        status, output = commands.getstatusoutput(cmd)
        end_time = time()

        os_status = os.WEXITSTATUS(status)

        testsuite.print_results(test['group'], test['test'], os_status, output)

        exec_time = end_time - start_time
        test_run_time_total = test_run_time_total + exec_time

        if options.print_exec_time:
            print_exec_time(testsuite, exec_time, "  Test execution time:")

    testsuite.debug("%s\n" % div) 

    if options.print_exec_time:
        print_exec_time(testsuite, test_run_time_total, "Total test execution:")
        testsuite.debug("\n") 

    testsuite.finish()

    status = cleanup_env(options.ip, options.virt)
    if status != PASS:
        print "Unable to clean up.  Please check your environment.\n"

    msg_body, heading = gen_report(options.virt, options.ip, testsuite.log_file)

    if options.report:
        print "Sending mail from %s to %s using %s relay.\n" % \
              (from_addr, to_addr, relay)
        send_report(to_addr, from_addr, relay, msg_body, heading)

if __name__ == '__main__':
    sys.exit(main())


