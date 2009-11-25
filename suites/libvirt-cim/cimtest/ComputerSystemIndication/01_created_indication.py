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
from os import waitpid, kill, fork, _exit, WNOHANG
from signal import SIGKILL
from time import sleep
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.classes import get_typed_class
from XenKvmLib.indication_tester import CIMIndicationSubscription
from XenKvmLib.vxml import set_default
from XenKvmLib.vxml import get_class

SUPPORTED_TYPES = ['Xen', 'XenFV', 'KVM']

test_dom = "domU"

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
        logger.info("Watching for %s", iname)
        ind_names[ind] = ind_name
        sub_list[ind] = sub

    return sub_list, ind_names, dict

def gen_ind(test_dom, ip, vtype, ind, cxml):
    if ind == "define":
        ret = cxml.cim_define(ip)
        if not ret:
            return FAIL 
        return PASS
    elif ind == "start":
        status = cxml.cim_start(ip)
        if status != PASS:
            logger.error("Failed to start domain: %s", test_dom)
            return FAIL
        return PASS
    elif ind == "destroy":
        ret = cxml.cim_destroy(ip)
        if not ret:
            logger.error("Unable to destroy %s", test_dom)
            return FAIL
        return PASS
        
    return FAIL 

def handle_request(sub, ind_name, dict, exp_ind_ct):
    #sfcb delivers indications to all registrations, even if the indication
    #isn't what the registration was subscribed to.  So, for modified and 
    #deleted indications, we must loop through until the indication we are
    #looking for is triggered.
    for i in range(0, exp_ind_ct):
        sub.server.handle_request() 
        if len(sub.server.indications) < 1:
            logger.error("No valid indications received")
            return FAIL

        if str(sub.server.indications[0]) == ind_name:
                sub.unsubscribe(dict['default_auth'])
                logger.info("Cancelling subscription for %s", ind_name)
                return PASS
        else:
                sub.server.indications.remove(sub.server.indications[0])

    logger.error("Did not recieve indication %s", ind_name)
    return FAIL

def poll_for_ind(pid, ind_name):
    status = FAIL
    for i in range(0, 20):
        pw = waitpid(pid, WNOHANG)

        # If pid exits, waitpid returns [pid, return_code] 
        # If pid is still running, waitpid returns [0, 0]
        # Only return a success if waitpid returns the expected pid
        # and the return code is 0.
        if pw[0] == pid and pw[1] == 0:
            logger.info("Great, got %s indication successfuly", ind_name)
            status = PASS
            break
        elif pw[1] == 0 and i < 19:
            if i % 10 == 0:
                logger.info("In child, waiting for %s indication", ind_name)
            sleep(1)
        else:
            # Time is up and waitpid never returned the expected pid
            if pw[0] != pid:
                logger.error("Waited too long for %s indication", ind_name)
                kill(pid, SIGKILL)
            else:
                logger.error("Received indication error: %d", pw[1])

            status = FAIL
            break

    return status

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    ip = options.ip
    virt = options.virt
    status = FAIL

    sub_list, ind_names, dict = sub_ind(ip, virt)

    ind_list = ["define", "start", "destroy"]

    cxml = get_class(virt)(test_dom)

    for ind in ind_list:
        sub = sub_list[ind]
        ind_name = ind_names[ind]

        try:
            pid = fork()
            if pid == 0:
                status = handle_request(sub, ind_name, dict, len(ind_list))
                if status != PASS:
                    _exit(1)

                _exit(0)
            else:
                try:
                    status = gen_ind(test_dom, ip, virt, ind, cxml)
                    if status != PASS:
                        kill(pid, SIGKILL)
                        raise Exception("Unable to generate indication") 

                    status = poll_for_ind(pid, ind)
                    if status != PASS:
                        raise Exception("Poll for indication Failed")

                except Exception, details:
                    kill(pid, SIGKILL)
                    raise Exception(details)

        except Exception, details:
            logger.error("Exception: %s", details)
            status = FAIL

    #Make sure all subscriptions are really unsubscribed
    for ind, sub in sub_list.iteritems():
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s", ind_names[ind])
       
    cxml.undefine(ip)

    return status

if __name__=="__main__":
    sys.exit(main())
