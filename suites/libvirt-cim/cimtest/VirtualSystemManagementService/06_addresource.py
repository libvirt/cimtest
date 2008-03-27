#!/usr/bin/python
#
# Copyright 2008 IBM Corp.
#
# Authors:
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

import sys
import pywbem
from pywbem.cim_obj import CIMInstanceName
from VirtLib import utils
from XenKvmLib import vsms
from XenKvmLib import vxml
from XenKvmLib.classes import get_typed_class
from CimTest.Globals import log_param, logger
from CimTest.Globals import do_main
from CimTest.ReturnCodes import FAIL, PASS

sup_types = ['Xen', 'KVM']
default_dom = 'rstest_domain'
nnmac = '99:aa:bb:cc:ee:ff'
npvcpu = 2

@do_main(sup_types)
def main():
    options = main.options
    log_param()

    if options.virt == 'KVM':
        nddev = 'hdb'
    else:
        nddev = 'xvdb'

    service = vsms.get_vsms_class(options.virt)(options.ip)
    cxml = vxml.get_class(options.virt)(default_dom)
    classname = get_typed_class(options.virt, 'VirtualSystemSettingData')
    vssd_ref = CIMInstanceName(classname, keybindings = {
                               'InstanceID' : '%s:%s' % (options.virt, default_dom),
                               'CreationClassName' : classname})
    dasd = vsms.get_dasd_class(options.virt)(dev=nddev,
                                             source=cxml.secondary_disk_path,
                                             name=default_dom)
    nasd = vsms.get_nasd_class(options.virt)(type='ethernet', mac=nnmac,
                                             name=default_dom)
    pasd = vsms.get_pasd_class(options.virt)(vcpu=npvcpu, name=default_dom)

    status = FAIL
    try:
        cxml.define(options.ip)
        # Add disk resource setting
        service.AddResourceSettings(AffectedConfiguration=vssd_ref, 
                                    ResourceSettings=[str(dasd)])
        cxml.dumpxml(options.ip)
        disk_dev = cxml.get_value_xpath(
                    '/domain/devices/disk/target/@dev[. = "%s"]' % nddev) 
        if disk_dev != nddev:
            raise Exception('Error adding rs for disk_dev')
        logger.info('good status for disk_dev')
        # Add net resource setting
        service.AddResourceSettings(AffectedConfiguration=vssd_ref,
                                    ResourceSettings=[str(nasd)])
        cxml.dumpxml(options.ip)
        net_mac = cxml.get_value_xpath(
                    '/domain/devices/interface/mac/@address[. = "%s"]' % nnmac)
        if net_mac.lower() != nnmac:
            raise Exception('Error adding rs for net_mac')
        logger.info('good status for net_mac')
        # Add processor resource setting
        service.AddResourceSettings(AffectedConfiguration=vssd_ref,
                                    ResourceSettings=[str(pasd)])
        cxml.dumpxml(options.ip)
        proc_vcpu = cxml.xml_get_vcpu()
        if int(proc_vcpu) != int(npvcpu):
            raise Exception('Error adding rs for proc_vcpu')
        logger.info('good status for proc_vcpu')
        status = PASS
    except Exception, details:
        logger.error('Error invoking AddRS')
        logger.error(details)
    finally:
        cxml.undefine(options.ip)

    return status

if __name__ == "__main__":
    sys.exit(main())
    
