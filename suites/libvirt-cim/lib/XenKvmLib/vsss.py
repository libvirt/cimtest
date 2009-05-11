#!/usr/bin/python
#
# Copyright 2009 IBM Corp.
#
# Authors:
#    Kaitlin Rupert <karupert@us.ibm.com>
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

import pywbem
from VirtLib.utils import run_remote 
from CimTest.Globals import logger
from CimTest.ReturnCodes import FAIL, PASS

#Path to snapshot save location
snapshot_save_loc = '/var/lib/libvirt/'

def remove_snapshot(ip, vm_name):
    snapshot = "%s%s" % (snapshot_save_loc, vm_name)

    cmd = "rm %s.save" % snapshot
    ret, out = run_remote(ip, cmd)
    if ret != 0:
        logger.error("Failed to remove snapshot file for %s", vm_name)
        return FAIL

    return PASS
