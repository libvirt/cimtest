#
# Copyright 2008 IBM Corp.
#
# Authors:
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

import os
import platform
import traceback
from optparse import OptionParser
from VirtLib.live import fv_cap
from CimTest.Globals import CIM_IP
from pywbem import WBEMConnection
from XenKvmLib.classes import get_typed_class

platform_sup = ["Xen", "KVM", "XenFV"]

VIRSH_ERROR_DEFINE = "Failed to define a domain with the name %s from virsh"

# vxml.NetXML
default_bridge_name = 'testbridge'
default_network_name = 'cimtest-networkpool'
default_net_type = 'network'

#vxml.PoolXML
default_pool_name = 'cimtest-diskpool'

# vxml.VirtXML
default_domname = 'domU1'
default_memory = 128
default_vcpus = 1
default_mallocunits="MegaBytes"


_image_dir = '/tmp'

# vxml.XenXML
Xen_kernel_path = os.path.join(_image_dir, 'default-xen-kernel')
Xen_init_path = os.path.join(_image_dir, 'default-xen-initrd')
Xen_disk_path = os.path.join(_image_dir, 'default-xen-dimage')
Xen_secondary_disk_path = os.path.join(_image_dir, 'default-xen-dimage.2ND')
Xen_default_disk_dev = 'xvda'
Xen_default_mac = '11:22:33:aa:bb:cc'

# vxml.KVMXML
if fv_cap(CIM_IP):
    KVM_default_emulator = '/usr/bin/qemu-kvm'
else:
    KVM_default_emulator = '/usr/bin/qemu'
KVM_disk_path = os.path.join(_image_dir, 'default-kvm-dimage')
KVM_secondary_disk_path = os.path.join(_image_dir, 'default-kvm-dimage.2ND')
KVM_default_disk_dev = 'hda'
KVM_default_mac = '11:22:33:aa:bb:cc'

# vxml.XenFVXML
s, o = platform.architecture()
if o == '32bit':
    arch = 'lib'
else:
    arch = 'lib64'
XenFV_default_loader = '/usr/lib/xen/boot/hvmloader'
XenFV_default_emulator = '/usr/%s/xen/bin/qemu-dm' % arch
XenFV_disk_path = os.path.join(_image_dir, 'default-kvm-dimage')
XenFV_secondary_disk_path = os.path.join(_image_dir, 'default-kvm-dimage.2ND')
XenFV_default_disk_dev = 'hda'
XenFV_default_mac = '00:16:3e:5d:c7:9e'

#vxml.LXCXML
LXC_init_path = os.path.join(_image_dir, 'cimtest_lxc_init')
LXC_default_tty = '/dev/ptmx'
LXC_default_mp = '/tmp'
LXC_default_source = '/tmp/lxc_files'
LXC_default_mac = '11:22:33:aa:bb:cc'
LXC_netns_support = False  

parser = OptionParser()
parser.add_option("-i", "--ip", dest="ip", default="localhost",
                  help="IP address of machine to test, default: localhost")
parser.add_option("-v", "--virt", dest="virt", type="choice",
                  choices=['Xen', 'KVM', 'XenFV', 'LXC'], default="Xen",
                  help="Virt type, select from: 'Xen' & 'KVM' & 'XenFV' & 'LXC', default: Xen")
parser.add_option("-d", "--debug-output", action="store_true", dest="debug",
                  help="Duplicate the output to stderr")


def do_main(types=['Xen'], p=parser):
    def do_type(f):
        import sys
        from CimTest.ReturnCodes import SKIP, FAIL
        (options, args) = p.parse_args()
        if options.virt not in types:
            return lambda:SKIP
        else:
            def do_try():
                try:
                    from CimTest.Globals import logger, log_param 
                    log_param()
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


def get_provider_version(virt, ip):
    conn = WBEMConnection('http://%s' % ip,
                          (os.getenv('CIM_USER'), os.getenv('CIM_PASS')),
                          os.getenv('CIM_NS'))
    vsms_cn = get_typed_class(virt, 'VirtualSystemManagementService')
    try:
        inst = conn.EnumerateInstances(vsms_cn)
        revision = inst[0]['Revision']
        changeset = inst[0]['Changeset']
    except Exception:
        return 0, "Unknown" 

    if revision is None or changeset is None:
        return 0, "Unknown" 

    revision = revision.strip("+")
    if revision.isdigit():
        revision = int(revision)

    return revision, changeset 


