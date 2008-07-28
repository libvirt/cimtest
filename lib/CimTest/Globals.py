#
# Copyright 2008 IBM Corp. 
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
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
import os
import logging
from optparse import OptionParser
import traceback

global CIM_USER
global CIM_PASS
global CIM_NS
global CIM_LEVEL
global CIM_FUUID
global platform_sup
global CIM_IP
global CIM_PORT

global CIM_ERROR_ASSOCIATORNAMES
global CIM_ERROR_ENUMERATE
global CIM_ERROR_GETINSTANCE
global VIRSH_ERROR_DEFINE

CIM_USER  = os.getenv("CIM_USER")
CIM_PASS  = os.getenv("CIM_PASS")
CIM_NS    = os.getenv("CIM_NS")
CIM_LEVEL = os.getenv("CIM_LEVEL")
CIM_FUUID = os.getenv("CIM_FUUID")
CIM_TC    = os.getenv("CIM_TC")
CIM_IP    = os.getenv("CIM_IP")
CIM_PORT = "5988"
NM = "TEST LOG"
platform_sup = ["Xen", "KVM", "XenFV"]
logging.basicConfig(filename='/dev/null')
logger = logging.getLogger(NM)
logging.PRINT = logging.DEBUG + 50
logging.addLevelName(logging.PRINT, "PRINT")


CIM_ERROR_ENUMERATE        = "Failed to enumerate the class of %s"
CIM_ERROR_GETINSTANCE      = "Failed to get instance by the class of %s"
CIM_ERROR_ASSOCIATORS      = "Failed to get associators information for %s"
CIM_ERROR_ASSOCIATORNAMES  = "Failed to get associatornames according to %s"
VIRSH_ERROR_DEFINE         = "Failed to define a domain with the name %s from virsh"

parser = OptionParser()
parser.add_option("-i", "--ip", dest="ip", default="localhost", 
                  help="IP address of machine to test, default: localhost")
parser.add_option("-v", "--virt", dest="virt", type="choice",
                  choices=['Xen', 'KVM', 'XenFV', 'LXC'], default="Xen",
                  help="Virt type, select from: 'Xen' & 'KVM' & 'XenFV' & 'LXC', default: Xen")
parser.add_option("-d", "--debug-output", action="store_true", dest="debug",
                  help="Duplicate the output to stderr")

if not CIM_NS:
    CIM_NS = "root/cimv2"

if not CIM_LEVEL:
    CIM_LEVEL=logging.PRINT
else:
    CIM_LEVEL = os.getenv("CIM_LEVEL")

if not CIM_FUUID:
    CIM_FUUID = "/tmp/cimtest.uuid"

if not CIM_TC:
    CIM_TC = " " 
if not CIM_IP:
    CIM_IP = "localhost"


def log_param(debug=None):
    #FIXME debug=None is a temporary work around to avoid duplicate
    # logging in vsmtest.log because we have log_param in both the
    # do_main decorator and the test case's main function.
    # We can safely delete the if branch here after all test cases
    # have removed the log_param invoke.
    if debug == None:
        return
    else:
        logger.setLevel(logging.DEBUG)
        #create console handler and set level to debug
        ch = logging.StreamHandler()
        if debug:
            ch.setLevel(logging.ERROR)
        else:
            ch.setLevel(int(CIM_LEVEL))
        #create file handler and set level to debug
        fh = logging.FileHandler("vsmtest.log")
        fh.setLevel(logging.DEBUG)
        #create formatter
        formatter = logging.Formatter(\
                "%(asctime)s:%(name)s:%(levelname)s   \t-  %(message)s",
                datefmt="%a, %d %b %Y %H:%M:%S")
        #add formatter to handlers
        fh.setFormatter(formatter)
        formatter = logging.Formatter("%(levelname)s \t- %(message)s")
        ch.setFormatter(formatter)
        #add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        #Print header
        logger.info("====%s Log====", CIM_TC)

def log_bug(bug_num):
    logger.info("Known Bug:%s" % bug_num)
    print "Bug:<%s>" % bug_num

def do_main(types=['Xen'], p=parser):
    def do_type(f):
        import sys
        from ReturnCodes import SKIP, FAIL
        (options, args) = p.parse_args()
        if options.virt not in types:
            return lambda:SKIP
        else:
            def do_try():
                try:
                    log_param(options.debug==True)
                    from VirtLib.utils import setup_ssh_key
                    from XenKvmLib.test_doms import destroy_and_undefine_all
                    setup_ssh_key()
                    destroy_and_undefine_all(options.ip, options.virt)
                    rc = f()
                except Exception, e:
                    logger.error('%s : %s' % (e.__class__.__name__, e))
                    logger.error("%s" % traceback.print_exc())
                    rc = FAIL
                return rc
            setattr(do_try, 'options', options)
            return do_try
    return do_type

