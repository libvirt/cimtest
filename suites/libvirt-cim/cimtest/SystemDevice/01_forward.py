#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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

import sys
from VirtLib import utils
from XenKvmLib import assoc
from XenKvmLib import vxml
from XenKvmLib import devices
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import logger, do_main
from CimTest.ReturnCodes import PASS, FAIL

sup_types = ['Xen', 'KVM', 'XenFV']

test_dom = "test_domain"
test_mac = "00:11:22:33:44:55"
test_cpu = 1

@do_main(sup_types)
def main():
    options= main.options

    if options.virt == 'Xen':
        test_disk = 'xvdb'
    else:
        test_disk = 'hdb'

    status = PASS
    virt_xml = vxml.get_class(options.virt)
    cxml = virt_xml(test_dom, vcpus = test_cpu, mac = test_mac, disk = test_disk)
    ret = cxml.create(options.ip)
    if not ret:
        logger.error('Unable to create domain %s' % test_dom)
        return FAIL

    sd_classname = get_typed_class(options.virt, 'SystemDevice')
    cs_classname = get_typed_class(options.virt, 'ComputerSystem')

    devs = assoc.AssociatorNames(options.ip, sd_classname, cs_classname,
                                 virt=options.virt,
                                 Name=test_dom, CreationClassName=cs_classname)
    if devs == None:
        logger.error("System association failed")
        return FAIL
    elif len(devs) == 0:
        logger.error("No devices returned")
        return FAIL

    cn_devid = {
            get_typed_class(options.virt, "NetworkPort") : '%s/%s' % (test_dom, test_mac),
            get_typed_class(options.virt, "Memory")      : '%s/mem' % test_dom,
            get_typed_class(options.virt, "LogicalDisk") : '%s/%s' % (test_dom, test_disk),
            get_typed_class(options.virt, "Processor")   : '%s/%s' % (test_dom, test_cpu-1)
            }

    key_list = {'DeviceID' : '',
                'CreationClassName' : '',
                'SystemName' : test_dom,
                'SystemCreationClassname' : cs_classname
               }
 
    for dev_cn in cn_devid.keys():
        for dev in devs:
            key_list['CreationClassName'] = dev['CreationClassname']
            key_list['DeviceID'] = dev['DeviceID']
            device = devices.device_of(options.ip, key_list)
            if device.CreationClassName != dev_cn:
                continue
            devid = device.DeviceID

            _devid = cn_devid[dev_cn]
            if devid != _devid:
                logger.error("DeviceID `%s` != `%s'" % (devid, _devid))
                status = FAIL
            else:
                logger.info("Examined %s" % _devid)
            
    cxml.destroy(options.ip)
    cxml.undefine(options.ip)

    return status
        
if __name__ == "__main__":
    sys.exit(main())
