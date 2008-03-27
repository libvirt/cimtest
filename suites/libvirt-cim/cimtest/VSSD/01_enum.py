#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
#    Veerendra Chandrappa <vechandr@in.ibm.com>
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

# The following test case is used to verify the VSSD class 
# Date : 25-10-2007 

import sys
from VirtLib import live
from VirtLib import utils
from XenKvmLib import enumclass
from XenKvmLib.test_doms import destroy_and_undefine_all
from XenKvmLib.vxml import XenXML, KVMXML, get_class
from CimTest.Globals import do_main
from CimTest.Globals import log_param, logger

sup_types = ['Xen', 'KVM']

test_dom = "new"

@do_main(sup_types)
def main():
    options = main.options
    log_param()
    status = 0

    destroy_and_undefine_all(options.ip)
    vsxml = get_class(options.virt)(test_dom)
    ret = vsxml.define(options.ip)
    if not ret :
        logger.error("error while create of VS")
        status = 1

    try:
        live_cs = live.domain_list(options.ip, options.virt)
        key_list = ["InstanceID"]
        syslst = enumclass.enumerate(options.ip, \
                                     "VirtualSystemSettingData", \
                                     key_list, \
                                     options.virt) 

        found = 0
        for vssd in syslst :
            instid = "%s:%s" % (options.virt, test_dom)
            if vssd.InstanceID == instid:
                found = 1
                break
        if found == 1:
            if vssd.ElementName != test_dom:
                logger.error("Invalid ElementName- expecting %s, go %s" % 
                             test_dom, vssd.ElementName)
                test_domain_function(test_dom, options.ip, "undefine")
                return 1

            logger.info("Examining VSSD class for the Guest %s" % test_dom)
            try:
                name = vssd.ElementName
                idx = live_cs.index(name)
                del live_cs[idx]
            except BaseException, details:
                logger.error("Exception %s" % details)
                logger.error("Provider reports VSSD `%s', but xm does not" %
                             vssd.ElementName)
                status = 1

        else:
            logger.error("Missing VSSD instance for the system %s " % test_dom)
            status = 1

    except BaseException, details:
        logger.error("Exception %s" % details)
        status = 1

    vsxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())

