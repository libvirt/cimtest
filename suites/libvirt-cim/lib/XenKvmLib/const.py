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
from VirtLib.live import fv_cap
from CimTest.Globals import CIM_IP
from pywbem import WBEMConnection
from XenKvmLib.classes import get_typed_class

# vxml.NetXML
default_bridge_name = 'testbridge'
default_network_name = 'cimtest-networkpool'
default_net_type = 'network'

#vxml.PoolXML
default_pool_name = 'testpool'

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

    revision.strip("+")
    if revision.isdigit():
        revision = int(revision)

    return revision, changeset 


