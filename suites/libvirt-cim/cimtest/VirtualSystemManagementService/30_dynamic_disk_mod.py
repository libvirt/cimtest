#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Sharad Mishra <snmishra@us.ibm.com>
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from XenKvmLib import vsms
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from CimTest.ReturnCodes import FAIL, PASS, XFAIL
from XenKvmLib import vsms_util

sup_types = ['Xen', 'KVM', 'XenFV']
default_dom = 'rstest_domain'

@do_main(sup_types)
def main():
    options = main.options

    if options.virt == 'KVM':
        nddev = 'vdb'
    else:
        nddev = 'xvdb'

    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    classname = get_typed_class(options.virt, 'VirtualSystemSettingData')
    inst_id = '%s:%s' % (options.virt, default_dom)
    vssd_ref = CIMInstanceName(classname, keybindings = {
                               'InstanceID' : inst_id,
                               'CreationClassName' : classname})
    dasd = vsms.get_dasd_class(options.virt)(dev=nddev,
                                             source=cxml.secondary_disk_path,
                                             name=default_dom)
    disk_attr = { 'nddev' : nddev,
                  'src_path' : cxml.secondary_disk_path
                }

    cxml.undefine(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    ret = cxml.cim_define(options.ip)
    if not ret:
        logger.error("Failed to define the dom: %s", default_dom)
        return FAIL
  
    ret = cxml.start(options.ip)
    if not ret:
        logger.error("Failed to start the dom: %s", default_dom)
        return FAIL

    status = vsms_util.add_disk_res(options.ip, service, cxml, vssd_ref,
                                    dasd, disk_attr)
    if status != PASS:
        return XFAIL
    dasd = vsms.get_dasd_class(options.virt)(dev='vdc',
                                         instanceid='rstest_domain/vda',
                                         source='/home/rss.iso',
                                         name=default_dom)

    service = vsms.get_vsms_class(options.virt)(options.ip)
    output = service.ModifyResourceSettings(ResourceSettings = [str(dasd)])

    return status

if __name__ == "__main__":
    sys.exit(main())
    
