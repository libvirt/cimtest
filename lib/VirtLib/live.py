#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
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
import os
import utils
import socket

def available_bridges(ip):
    """Return a list of the available bridges in the running dom0.
    """

    cmd = 'brctl show | grep -v "bridge name" | awk "/^[^\\t]/ { print \$1 }"'

    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        return []

    return out.splitlines()

def exclude_vir_bridge(ip):
    cmd = 'brctl show | grep -v "bridge name" | grep -v vir | \
           grep -v vif | awk "/^[^\\t]/ { print \$1 }"'
    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        return []

    return out.splitlines()

def available_virt_bridge(ip):
    """Return a list of the available virtual bridges in the running dom0.
    """

    cmd = 'brctl show | grep -v "bridge name" | grep -v peth | awk "/^[^\\t]/ { print \$1 }"'

    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        return []

    return out.splitlines()

def create_disk_file(ip, size, diskfile) :
    """Creates a disk file 1MB block-size ,and if succsess returns disk created.
    """
    cmd =  "dd if=/dev/zero of=" + diskfile + " bs=1M count=" +  str(size)

    rc, out = utils.run_remote(ip, cmd)

    if rc != 0:
        return None
    return rc


def max_free_mem(server):
    """Function to get max free mem on dom0.

    Returns an int containing the value in MB.
    """

    xm_ret, mfm = utils.run_remote(server,
                    'xm info | awk -F ": " "/max_free_memory/ {print \$2}"')
    if xm_ret != 0:
        return None

    return int(mfm)

def fv_cap(server):
    cmd = 'egrep flags /proc/cpuinfo | uniq | egrep "vmx|svm"'
    ret, out = utils.run_remote(server, cmd)
    return ret == 0

def hostname(server):
    """To return the hostname of the cimserver"""

    ret, out = utils.run_remote(server, "hostname")

    if ret != 0:
        return None

    return out

def full_hostname(server):
    """To return the fully qualifiec domain name(FQDN) of the system"""

    return socket.gethostbyaddr(socket.gethostname())[0]
