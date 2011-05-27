#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
import tempfile
import os
from VirtLib import utils
from XenKvmLib.xm_virt_util import domain_list, virt2uri
from CimTest.Globals import CIM_FUUID

try:
    import uuid as _uuid
    def uuid():
        return str(_uuid.uuid1())
except ImportError:
    def uuid():
        from commands import getstatusoutput as run
        s, o = run('uuidgen')
        if s == 0:
            return o
        else:
            raise ImportError("Missing uuid library (and can't fake it)")

def define_test_domain(xml, server, virt="Xen"):
    name = tempfile.mktemp()

    f = file(name, "w")
    f.write(xml)
    f.close()

    cmd = "virsh -c %s define %s 2>/dev/null" % (virt2uri(virt), name)
    s, o = utils.run_remote(server, cmd)

    return s == 0

def undefine_test_domain(name, server, virt="Xen"):
    cmd = "virsh -c %s undefine %s 2>/dev/null" % (virt2uri(virt), name)
    s, o = utils.run_remote(server, cmd)

    return s == 0

def start_test_domain(name, server, virt="Xen"):
    cmd = "virsh -c %s start %s 2>/dev/null" % (virt2uri(virt), name)
    s, o = utils.run_remote(server, cmd)

    return s == 0

def virdomid_list(server, virt="Xen"):
    """Get a list of domid from virsh"""
    
    cmd = 'virsh -c %s list 2>/dev/null | sed "1,2 d; /^$/d"' % \
                virt2uri(virt)
    ret, out = utils.run_remote(server, cmd)
    if ret != 0:
        return None

    ids = []
    lines = out.split("\n")
    for line in lines:
        dinfo=line.split()
        if len(dinfo) > 0:
            ids.append(dinfo[0])

    return ids

def set_uuid(myuuid=0):
    """Generate a random uuid and record it into CIM_FUUID"""

    if myuuid == 0:
        myuuid = uuid()

    f = file(CIM_FUUID, 'a')
    f.write('%s\n' % myuuid)
    f.close()

    return myuuid

def get_uuid_list():
    """Get a list of uuid from CIM_FUUID"""
    try:
        f = file(CIM_FUUID, 'r')
        mylist = [x.rstrip('\n') for x in f.readlines()]
        f.close()
        os.unlink(CIM_FUUID)
    except Exception, detail:
        mylist = []

    return mylist

def viruuid(name, server, virt="Xen"):
    """Return domain uuid given domid or domname"""
    cmd = 'virsh -c %s domuuid %s 2>/dev/null | sed "/^$/d"' % \
                (virt2uri(virt), name)
    ret, out = utils.run_remote(server, cmd)
    if ret == 0:
        return out.strip(" \n")
    else:
        return 0

def destroy_and_undefine_domain(name, server, virt="Xen"):
    """Destroy and undefine a domain.
    name could be domid or domname"""
    cmd = 'virsh -c %s "destroy %s ; undefine %s" 2>/dev/null' % \
                (virt2uri(virt), name, name)
    utils.run_remote(server, cmd)

def destroy_and_undefine_all(server, virt="Xen", aggressive = False):
    """Destroy and undefine all domain to keep a 
    clean env for next testcase"""
    
    names = domain_list(server, virt)
    ids = virdomid_list(server, virt)
    names.extend(ids)
    uuid_list = get_uuid_list()

    for name in names:
        if aggressive or viruuid(name, server, virt) in uuid_list:
            destroy_and_undefine_domain(name, server, virt)


# The following are the inputs to the function:
# xmlfile_domname = xml file name for define and create command
#                   Domname otherwise
# server          = IP Address of machine to test
# cmd             = define, create, suspend, destroy
#
 
def test_domain_function(xmlfile_domname, server, cmd, virt="Xen"):

    if cmd == "define" or cmd == "create":
        f = tempfile.NamedTemporaryFile('w') 
        f.write(xmlfile_domname)
        f.flush()
        name = f.name 
    else:
        name = xmlfile_domname

    vcmd = "virsh -c %s %s %s 2>/dev/null" % (virt2uri(virt), cmd, name)
    s, o = utils.run_remote(server, vcmd)
    if cmd == "define" or cmd == "create":
        f.close()
    return s == 0

def vir_cpu_list(name_id, server, virt="Xen"):
    """
       Get the vcpu lists. The input is either the domid or domname.
    """
    cmd = 'virsh -c %s vcpuinfo %s 2>/dev/null | grep "^$" | wc -l' % \
                (virt2uri(virt), name_id)
    ret, out = utils.run_remote(server, cmd)

    if ret != 0:
        return -1
    try:
        return out
    except (IndexError, ValueError):
        return -1

def create_vnet(server, net_xml, virt="Xen"):
    nf = tempfile.NamedTemporaryFile('w') 
    nf.write(net_xml)
    nf.flush()
    fname = nf.name
    cmd = "virsh -c %s net-create %s 2>/dev/null" % (virt2uri(virt), fname)
    ret, out = utils.run_remote(server, cmd)
    nf.close()
    if ret != 0:
        return -1
    return ret == 0 
