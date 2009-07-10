#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com>
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
#

from signal import SIGKILL
from CimTest.Globals import logger
from XenKvmLib.indication_tester import CIMIndicationSubscription
from XenKvmLib.vxml import set_default
from XenKvmLib.classes import get_typed_class
from CimTest.ReturnCodes import PASS, FAIL
from os import waitpid, kill, WNOHANG

def sub_ind(ip, virt, ind_names):
    dict = set_default(ip)
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

def poll_for_ind(pid, ind_name, timeout=20):
    status = FAIL
    for i in range(0, timeout):
        pw = waitpid(pid, WNOHANG)

        # If pid exits, waitpid returns [pid, return_code] 
        # If pid is still running, waitpid returns [0, 0]
        # Only return a success if waitpid returns the expected pid
        # and the return code is 0.
        if pw[0] == pid and pw[1] == 0:
            logger.info("Great, got '%s' indication successfully", ind_name)
            status = PASS
            break
        elif pw[1] == 0 and i < timeout:
            if i % 10 == 0:
                logger.info("In child, waiting for '%s' indication", ind_name)
            sleep(1)
        else:
            # Time is up and waitpid never returned the expected pid
            if pw[0] != pid:
                logger.error("Waited too long for '%s' indication", ind_name)
                kill(pid, SIGKILL)
            else:
                logger.error("Received Indication error: '%d'", pw[1])

            status = FAIL
            break

    return status
