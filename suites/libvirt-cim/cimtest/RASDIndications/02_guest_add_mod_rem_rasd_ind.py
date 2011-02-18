#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#   Deepti B. Kalakeri <deeptik@linux.vnet.ibm.com> 
#    
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
# This testcase is used to verify the Created|Modified|Deleted 
# RASD Indications for a guest.
#
#                                                      Date : 21-09-2009
#

import sys
from signal import SIGKILL
from XenKvmLib import vsms
from XenKvmLib import vsms_util
from XenKvmLib.classes import get_typed_class
from XenKvmLib.enumclass import EnumNames
from socket import gethostname
from os import kill, fork, _exit
from XenKvmLib.vxml import get_class
from CimTest.Globals import logger
from XenKvmLib.const import do_main, CIM_DISABLE, get_provider_version
from CimTest.ReturnCodes import PASS, FAIL, SKIP
from XenKvmLib.common_util import poll_for_state_change 
from XenKvmLib.indications import sub_ind, handle_request, poll_for_ind

sup_types = ['KVM', 'Xen', 'XenFV']
libvirt_guest_rasd_indication_rev = 980

nmem = 131072
nmac = '00:11:22:33:44:55'

def create_guest(test_dom, ip, virt, cxml):
    try:
        ret = cxml.cim_define(ip)
        if not ret:
            raise Exception("Failed to define domain %s" % test_dom)

        status, dom_cs = poll_for_state_change(ip, virt, test_dom,
                                               CIM_DISABLE)
        if status != PASS:
            raise Exception("Dom '%s' not in expected state '%s'" \
                            % (test_dom, CIM_DISABLE))

    except Exception, details:
        logger.error("Exception details: %s", details)
        return FAIL, cxml

    return PASS, cxml


def get_rasd_rec(virt, cn, s_sysname, inst_id):
    classname = get_typed_class(virt, cn)
    recs = EnumNames(s_sysname, classname)
    rasd = None
    for rasd_rec in recs: 
        ret_pool = rasd_rec['InstanceID']
        if ret_pool == inst_id:
            rasd = rasd_rec 
            break

    return rasd

def gen_indication(test_dom, s_sysname, virt, cxml, service, ind_name,
                   rasd=None, nmem_disk=None):
    status = FAIL

    if virt == "XenFV":
        prefix = "Xen"
    else:
        prefix = virt
 
    try:

        if ind_name == "add":
            cn = 'VirtualSystemSettingData'
            inst_id = '%s:%s' % (prefix, test_dom)
            classname = get_typed_class(virt, cn)
            vssd_ref = get_rasd_rec(virt, cn, s_sysname, inst_id)

            if vssd_ref == None:
                raise Exception("Failed to get vssd_ref for '%s'" % test_dom)

            status = vsms_util.add_disk_res(s_sysname, service, cxml, 
                                            vssd_ref, rasd, nmem_disk)

        elif ind_name == "modify":
            status = vsms_util.mod_mem_res(s_sysname, service, cxml, 
                                           rasd, nmem_disk)

        elif ind_name == 'delete':
            cn = 'GraphicsResourceAllocationSettingData'
            inst_id = '%s/%s' % (test_dom, "graphics")
            classname = get_typed_class(virt, cn)
            nrasd = get_rasd_rec(virt, cn, s_sysname, inst_id)

            if nrasd == None:
                raise Exception("Failed to get nrasd for '%s'" % test_dom)

            res = service.RemoveResourceSettings(ResourceSettings=[nrasd])
            status = res[0]
       
    except Exception, details:
        logger.error("Exception details :%s", details)
        return FAIL

    return status

@do_main(sup_types)
def main():
    options = main.options
    virt = options.virt
    s_sysname = options.ip

    cim_rev, changeset = get_provider_version(virt, s_sysname)
    if cim_rev < libvirt_guest_rasd_indication_rev:
        logger.info("Support for Guest Resource Indications is available in "
                    "Libvirt-CIM rev '%s'", libvirt_guest_rasd_indication_rev)
        return SKIP

    status = FAIL
    test_dom = 'VM_' + gethostname()
    ind_names = {
                 'add'    : 'ResourceAllocationSettingDataCreatedIndication',
                 'modify' : 'ResourceAllocationSettingDataModifiedIndication',
                 'delete' : 'ResourceAllocationSettingDataDeletedIndication'
                }

    sub_list, ind_names, dict = sub_ind(s_sysname, virt, ind_names)
    virt_xml = get_class(virt)
    cxml = virt_xml(test_dom, mac=nmac)
    service = vsms.get_vsms_class(options.virt)(options.ip)
    ndpath = cxml.secondary_disk_path

    if virt == 'KVM':
        nddev = 'hdb'
    else:
        nddev = 'xvdb'

    disk_attr = { 'nddev' : nddev,
                  'src_path' : ndpath 
                }
    dasd = vsms.get_dasd_class(options.virt)(dev=nddev,
                                             source=cxml.secondary_disk_path,
                                             name=test_dom)
    masd = vsms.get_masd_class(options.virt)(megabytes=nmem, name=test_dom)
    rasd_info = { 'add' : [dasd, disk_attr], 
                  'modify' : [masd, nmem] 
                }

    status, cxml = create_guest(test_dom, s_sysname, virt, cxml)
    if status != PASS:
        logger.error("Error setting up the guest '%s'" % test_dom)
        return FAIL

    for ind in ind_names.keys():
        sub = sub_list[ind]
        ind_name = ind_names[ind]
        logger.info("\n Verifying '%s' indications ....", ind_name)
        
        try:
            pid = fork()
            if pid == 0:
                status = handle_request(sub, ind_name, dict, 
                                        len(ind_names.keys()))
                if status != PASS:
                    _exit(1)

                _exit(0)
            else:
                try:
                    if ind != 'delete':
                        rasd = rasd_info[ind][0]
                        val  = rasd_info[ind][1]
                        status = gen_indication(test_dom, s_sysname, 
                                                      virt, cxml, service,
                                                      ind, rasd, val)
                    else:
                        status = gen_indication(test_dom, s_sysname, 
                                                      virt, cxml, service,
                                                      ind)
                    if status != PASS:
                        raise Exception("Unable to generate indication") 
       
                    status = poll_for_ind(pid, ind_name)
                    if status != PASS:
                        raise Exception("Poll for indication Failed")

                except Exception, details:
                    kill(pid, SIGKILL)
                    raise Exception(details)

        except Exception, details:
            logger.error("Exception: %s", details)
            status = FAIL

        if status != PASS:
            break
        
	    #Make sure all subscriptions are really unsubscribed
    for ind, sub in sub_list.iteritems():
        sub.unsubscribe(dict['default_auth'])
        logger.info("Cancelling subscription for %s", ind_names[ind])

    ret = cxml.undefine(s_sysname)
    if not ret:
        logger.error("Failed to undefine the domain '%s'", test_dom)
        return FAIL

    return status
if __name__ == "__main__":
    sys.exit(main())

