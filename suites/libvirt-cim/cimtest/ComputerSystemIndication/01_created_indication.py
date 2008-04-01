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
from CimTest.Globals import log_param, logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import PASS, FAIL
from XenKvmLib.common_util import create_using_definesystem 
from XenKvmLib.test_doms import undefine_test_domain
from XenKvmLib.classes import get_typed_class
from XenKvmLib.indication_tester import CIMIndicationSubscription
from XenKvmLib.vxml import set_default

SUPPORTED_TYPES = ['Xen', 'XenFV', 'KVM']

test_dom = "domU"

@do_main(SUPPORTED_TYPES)
def main():
    options = main.options
    log_param()
    status = FAIL

    dict = set_default(options.ip)
    indication_name = get_typed_class(options.virt, 'ComputerSystemCreatedIndication')
    
    sub = CIMIndicationSubscription(dict['default_name'], indication_name, dict['default_ns'],
                                    dict['default_print_ind'], dict['default_sysname'])
    sub.subscribe(dict['default_url'], dict['default_auth'])
    logger.info("Watching for %s" % indication_name)
     
    try:
        pid = os.fork()
        if pid == 0:
            sub.server.handle_request() 
            if len(sub.server.indications) == 0:
                logger.error("No valid indications received")
                sys.exit(1)
            elif str(sub.server.indications[0]) != indication_name:
                logger.error("Received indication %s instead of %s" % (indication_name, str(sub.server.indications[0])))
                sys.exit(2)
            else:
                sys.exit(0)
        else:
            create_using_definesystem(test_dom, options.ip, None, None, options.virt)
            for i in range(0,100):
                pw = os.waitpid(pid, os.WNOHANG)[1]
                if pw == 0:
                    logger.info("Great, got indication successfuly")
                    status = PASS
                    break
                elif pw == 1 and i < 99:
                    logger.info("still in child process, waiting for indication")
                    time.sleep(1)
                else:
                    logger.error("Received indication error or wait too long")
                    break 
    except Exception, details:
            logger.error("Unknown exception happened")
            logger.error(details)
    finally:    
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s" % indication_name)
        os.kill(pid, signal.SIGKILL)
        undefine_test_domain(test_dom, options.ip, options.virt)

    return status

if __name__=="__main__":
    sys.exit(main())
