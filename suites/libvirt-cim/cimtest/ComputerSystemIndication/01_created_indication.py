#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
# 
# Authors:
#     Guolian Yun <yunguol@cn.ibm.com>
# 
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
# 
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
# 
#  You should have received a copy of the GNU General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
# 

import sys
import os
import signal
import time
from pywbem.cim_obj import CIMInstanceName
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import create_using_definesystem, \
                                  call_request_state_change
from XenKvmLib.test_doms import destroy_and_undefine_domain 
from XenKvmLib.classes import get_typed_class
from XenKvmLib.indication_tester import CIMIndicationSubscription
from XenKvmLib.vxml import set_default
from XenKvmLib.vsms import get_vsms_class

SUPPORTED_TYPES = ['Xen', 'XenFV', 'KVM']

test_dom = "domU"
REQ_STATE = 2
TIME = "00000000000000.000000:000"

def sub_ind(ip, virt):
    dict = set_default(ip)
    ind_names = {"define" : 'ComputerSystemCreatedIndication', 
                 "start" : 'ComputerSystemModifiedIndication',
                 "destroy" : 'ComputerSystemDeletedIndication'
                }

    sub_list = {}
    port = 5

    for ind, iname in ind_names.iteritems():
        ind_name = get_typed_class(virt, iname)

        sub_name = "Test%s" % ind_name
        port += 1

        sub = CIMIndicationSubscription(sub_name, ind_name,
                                        dict['default_ns'],
                                        dict['default_print_ind'],
                                        dict['default_sysname'],
                                        port)
        sub.subscribe(dict['default_url'], dict['default_auth'])
        logger.info("Watching for %s" % iname)
        ind_names[ind] = ind_name
        sub_list[ind] = sub

    return sub_list, ind_names, dict

def gen_ind(test_dom, ip, vtype, ind):
    if ind == "define":
        return create_using_definesystem(test_dom, ip, virt=vtype)

    elif ind == "start":
        rc = call_request_state_change(test_dom, ip, REQ_STATE, TIME, vtype)
        if rc != 0:
            logger.error("Failed to start domain: %s" % test_dom)
            return FAIL
        return PASS

    elif ind == "destroy":
        service = get_vsms_class(vtype)(ip)
        try:
            classname = get_typed_class(vtype, 'ComputerSystem')
            cs_ref = CIMInstanceName(classname, keybindings = {
                                     'Name':test_dom,
                                     'CreationClassName':classname})
            service.DestroySystem(AffectedSystem=cs_ref)
        except Exception, details:
            logger.error('Unknow exception happened')
            logger.error(details)
            return FAIL
        return PASS
        
    return FAIL 

def handle_request(sub, ind_name):
    sub.server.handle_request() 
    if len(sub.server.indications) == 0:
        logger.error("No valid indications received")
        return FAIL
    elif str(sub.server.indications[0]) != ind_name:
        logger.error("Received indication %s instead of %s" % \
                     (str(sub.server.indications[0])), ind_name)
        return FAIL

    return PASS

def poll_for_ind(pid):
    for i in range(0, 20):
        pw = os.waitpid(pid, os.WNOHANG)

        # If pid exits, waitpid returns [pid, return_code] 
        # If pid is still running, waitpid returns [0, 0]
        # Only return a success if waitpid returns the expected pid
        # and the return code is 0.
        if pw[0] == pid and pw[1] == 0:
            logger.info("Great, got indication successfuly")
            status = PASS
            break
        elif pw[1] == 0 and i < 19:
            if i % 10 == 0:
                logger.info("In child process, waiting for indication")
            time.sleep(1)
        else:
            # Time is up and waitpid never returned the expected pid
            if pw[0] != pid:
                logger.error("Waited too long for indication")
                os.kill(pid, signal.SIGKILL)
            else:
                logger.error("Received indication error: %d" % pw[1])

            status = FAIL
            break

    return status

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    status = FAIL

    sub_list, ind_names, dict = sub_ind(options.ip, options.virt)

    ind_list = ["define", "start", "destroy"]

    for ind in ind_list:
        sub = sub_list[ind]
        ind_name = ind_names[ind]

        try:
            pid = os.fork()
            if pid == 0:
                status = handle_request(sub, ind_name)
                if status != PASS:
                    os._exit(1)

                os._exit(0)
            else:
                try:
                    status = gen_ind(test_dom, options.ip, options.virt, ind)
                    if status != PASS:
                        os.kill(pid, signal.SIGKILL)
                        return FAIL

                    status = poll_for_ind(pid)
                except Exception, details:
                    logger.error("Exception: %s" % details)
                    os.kill(pid, signal.SIGKILL)
                    return FAIL

        except Exception, details:
            logger.error("Exception: %s" % details)
            return FAIL

    for ind, sub in sub_list.iteritems():
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s" % ind_names[ind])
       
    destroy_and_undefine_domain(test_dom, options.ip, options.virt)

    return status

if __name__=="__main__":
    sys.exit(main())
