#!/usr/bin/env python
#
# Copyright 2011 IBM Corp.
#
# Authors:
#    Eduardo Lima (Etrunko) <eblima@br.ibm.com>
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
# CIMTest Filter Lists Create
#

import sys
import helper

import pywbem

from CimTest.ReturnCodes import PASS, FAIL, XFAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main
from XenKvmLib.vxml import get_class
from VirtLib.utils import run_remote

sup_types = ["KVM",]

domain = None

def get_filter_inst_and_inst_name(name):
    try:
        _filters = test.libvirt_filter_lists()
        _id = test.id_for_filter_name(_filters, name)
    except Exception, e:
        # TODO: define a filter of our own
        logger.error("'%s' filter list not found in libvirt:\n%s", name, e)
        raise

    # Retrieve instance name for "clean-traffic"
    try:
        inst_name = test.FindInstanceName(name)
    except Exception, e:
        logger.error("'%s' filter list not found in libvirt-cim\n%s", name, e)
        raise

    # Retrieve instance for "clean-traffic"
    inst = test.GetInstance(inst_name)

    if not inst:
        logger.error("Unable to retrieve instance for '%s' filter list", name)
        raise Exception()
    elif inst["InstanceID"] != _id:
        logger.error("'%s' ids from libvirt and libvirt-cim differ", name)
        raise Exception()

    return inst, inst_name
# get_filter_inst_and_inst_name


def create_filter_list(name):
    # Get "clean-traffic" filter instance and instance name
    clean, clean_name = get_filter_inst_and_inst_name("clean-traffic")

    # Check if filter list already exist then delete it
    try:
        inst_name = test.FindInstanceName(name)
        test.wbem.DeleteInstance(inst_name)
        logger.info("Instance with name '%s' already exists. Deleting.", name)
    except:
        logger.info("No previous Instance with name '%s' found.", name)

    # Create a new FilterList instance based on name parameter
    global flist_name
    logger.info("Creating FilterList '%s'", name)
    flist_name = test.CreateFilterListInstance(name)
    flist = test.GetInstance(flist_name)

    # A NestedFilterList instance will add the "clean-traffic" filter
    # as an entry of the newly created FilterList
    logger.info("Creating NestedFilterList instance")
    nested_name = test.CreateFilterListInstance(None, "KVM_NestedFilterList",
                                  {"Antecedent":flist_name,
                                   "Dependent":clean_name})

    logger.info("Got NestedFilterList name '%s'", nested_name)
    #nested = test.GetInstance(nested_name)
    #logger.info("Got NestedFilterList '%s'", nested)

    # Check if results match
    _id, _name = [f for f in test.libvirt_filter_lists() if f[1] == name][0]
    elements = test.libvirt_filter_dumpxml(_id)
    filterref = [e for e in elements if e.tag == "filterref"][0]
    if clean["Name"] != filterref.get("filter"):
        raise Exception("NestedFilterList name and libvirt filter don't match")

    logger.info("NestedFilterList created successfuly")
    return flist, flist_name
# create_filter_list


def get_nwport_inst_and_inst_name(domain_name):
    try:
        inst_name = test.FindInstanceName(domain_name, "SystemName",
                                          "KVM_NetworkPort")
        inst = test.GetInstance(inst_name)
    except Exception, e:
        logger.error("Unable to get NetworkPort instance name for '%s' domain", domain_name)
        raise

    return inst, inst_name
#get_nwport_inst_and_inst_name


def cleanup():
    try:
        # Destroy filter list
        test.wbem.DeleteInstance(flist_name)
    except Exception, e:
        logger.error("Error deleting filter list: %s", e)

    try:
        # Destroy domain
        if domain:
            domain.destroy()
            domain.undefine()
    except Exception, e:
        logger.error("Error destroying domain: %s", e)
# cleanup


@do_main(sup_types)
def main():
    result = XFAIL
    options = main.options

    test_flist = "cimtest-filterlist"

    global test
    test = helper.FilterListTest(options.ip, options.virt)

    try:
        # Create a new FilterList instance
        flist, flist_name = create_filter_list(test_flist)

        # Create a new domain (VM)
        domain_name = "cimtest-filterlist-domain"
        global domain
        domain = helper.CIMDomain(domain_name, test.virt, test.server)
        domain.define()

        # Get NetworkPort instance and instance name for defined domain
        nwport, nwport_name = get_nwport_inst_and_inst_name(domain_name)

        # An AppliedFilterList Instance will apply the filter to the network
        # port of the defined domain
        test.CreateFilterListInstance(None, "KVM_AppliedFilterList",
                                      {"Antecedent":nwport_name,
                                       "Dependent":flist_name})
    except Exception, e:
        logger.error("Caught exception: %s", e)
        result = FAIL

    # Check results

    # Cleanup
    cleanup()

    # Leftovers?
    try:
        inst = test.FindInstance(test_flist)
        logger.error("Leftovers in CIM FilterLists: %s", inst)
        result = FAIL
    except IndexError:
        pass

    try:
        filt = [f for f in test.libvirt_filter_lists() if f[1] == test_flist][0]
        logger.error("Leftovers in libvirt filters: %s", filt)
        result = FAIL
    except IndexError:
        pass

    return result
# main

if __name__ == "__main__":
    sys.exit(main())
