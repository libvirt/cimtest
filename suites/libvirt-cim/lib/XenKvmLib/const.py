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
from VirtLib.utils import run_remote 
from CimTest.Globals import CIM_IP
from pywbem import WBEMConnection
from XenKvmLib.classes import get_typed_class

platform_sup = ["Xen", "KVM", "XenFV"]

#Distro changeset values
f9_changeset="1fcf330fadf8+"
sles11_changeset="SLES_11"

VIRSH_ERROR_DEFINE = "Failed to define a domain with the name %s from virsh"

#CIM values for VS State transitions
CIM_ENABLE      = 2
CIM_DISABLE     = 3
CIM_SHUTDOWN    = 4
CIM_NOCHANGE    = 5
CIM_SUSPEND     = 6
CIM_PAUSE       = 9
CIM_REBOOT      = 10
CIM_RESET       = 11

# Default TimeoutPeriod param for CS.RequestedStateChange()
TIME           = "00000000000000.000000:000"

#KVMRedirectionSAP protocol values
KVMRedSAP_proto =  { 'raw' : 2, 'rdp' : 3, 'vnc' : 4 }

# CIM values for KVMRedirectionSAP.EnabledState 
CIM_SAP_ACTIVE_STATE  =  2
CIM_SAP_INACTIVE_STATE = 3
CIM_SAP_AVAILABLE_STATE = 6


# vxml.NetXML
default_bridge_name = 'testbr'
default_network_name = 'cimtest-networkpool'
default_net_type = 'network'

#vxml.PoolXML
default_pool_name = 'cimtest-diskpool'

# vxml.VirtXML
default_domname = 'domU1'
default_memory = 128
default_vcpus = 1
default_mallocunits="MegaBytes"


_image_dir = '/var/lib/libvirt/images'

# vxml.XenXML
Xen_kernel_path = os.path.join(_image_dir, 'default-xen-kernel')
Xen_init_path = os.path.join(_image_dir, 'default-xen-initrd')
Xen_disk_path = os.path.join(_image_dir, 'default-xen-dimage')
Xen_secondary_disk_path = os.path.join(_image_dir, 'default-xen-dimage.2ND')
Xen_default_disk_dev = 'xvda'
Xen_default_mac = '88:22:33:aa:bb:cc'

# vxml.KVMXML
KVM_default_emulator = '/usr/bin/qemu-system-x86_64'
KVM_disk_path = os.path.join(_image_dir, 'default-kvm-dimage')
KVM_secondary_disk_path = os.path.join(_image_dir, 'default-kvm-dimage.2ND')
KVM_default_disk_dev = 'vda'
KVM_default_cdrom_dev = 'hdc'
KVM_default_mac = '88:22:33:aa:bb:cc'

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
LXC_default_emulator = '/usr/libexec/libvirt_lxc'
LXC_default_tty = '/dev/ptmx'
LXC_default_mp = '/tmp'
LXC_default_source = '/var/lib/libvirt/images/lxc_files'
LXC_default_mac = '88:22:33:aa:bb:cc'
LXC_netns_support = False  

parser = OptionParser()
parser.add_option("-i", "--ip", dest="ip", default="localhost",
                  help="IP address of machine to test, default: localhost")
parser.add_option("-m", "--target_url", dest="t_url", default="localhost:5988",
                  help="URL of destination host for remote migration ")
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
                    from XenKvmLib.test_doms import destroy_and_undefine_all
                    destroy_and_undefine_all(options.ip, options.virt)
                    rc = f()
                except Exception, e:
                    logger.error('%s : %s', e.__class__.__name__, e)
                    logger.error("%s", traceback.print_exc())
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

    # This is a sloppy mechanism for detecting a distro defined revision value
    distro = None

    cmd = 'cat /etc/issue | grep "SUSE Linux Enterprise Server 11"'
    rc, out = run_remote(ip, cmd)
    if rc == 0:
        distro = "sles11"      

    if revision.find(".") == 0:
        if distro == "sles11":
            return 0, sles11_changeset 

    revision = revision.strip("+")
    if revision.isdigit():
        revision = int(revision)
    else:
        raise Exception("revision %s is not a digit", revision)

    return revision, changeset


