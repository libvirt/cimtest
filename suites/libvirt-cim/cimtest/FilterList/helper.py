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

import pywbem
import libvirt

import CimTest
from CimTest.Globals import logger

import XenKvmLib
from XenKvmLib.xm_virt_util import virt2uri
from XenKvmLib.classes import get_typed_class
from XenKvmLib.vxml import get_class

import VirtLib
from VirtLib.utils import run_remote

from lxml import etree

class BaseTestObject(object):

    def __init__(self, server, virt):
        self.server = server
        self.virt = virt
        self.typed_class = get_typed_class(virt, self.cim_basename)
        self.uri = virt2uri(virt)
        self.user = CimTest.Globals.CIM_USER
        self.passwd = CimTest.Globals.CIM_PASS
        self.namespace = CimTest.Globals.CIM_NS
        self.wbem = pywbem.WBEMConnection("http://%s" % server,
                                          (self.user, self.passwd),
                                          self.namespace)
        self.wbem.debug = True
    # __init__

    def EnumerateInstances(self, typed_class=None):
        if not typed_class:
            typed_class = self.typed_class

        return self.wbem.EnumerateInstances(typed_class)
    # EnumerateInstances

    def EnumerateInstanceNames(self, typed_class=None):
        if not typed_class:
            typed_class = self.typed_class

        return self.wbem.EnumerateInstanceNames(typed_class)
    # EnumerateInstanceNames

    def __assoc_args(self, assoc_class=None, result_class=None):
        kargs = {}
        if assoc_class:
            kargs["AssocClass"] = assoc_class

        if result_class:
            kargs["ResultClass"] = result_class

        return kargs
    # __assoc_args

    def Associators(self, typed_class=None, assoc_class=None, result_class=None):
        if not typed_class:
            typed_class = self.typed_class

        kargs = self.__assoc_args(assoc_class, result_class)

        if kargs:
            return self.wbem.Associators(typed_class, **kargs)

        return self.wbem.Associators(typed_class)
    # Associators

    def AssociatorNames(self, typed_class=None, assoc_class=None, result_class=None):
        if not typed_class:
            typed_class = self.typed_class

        kargs = self.__assoc_args(assoc_class, result_class)

        if kargs:
            return self.wbem.Associators(typed_class, **kargs)

        return self.wbem.AssociatorNamess(typed_class)
    # AssociatorNames

    def GetInstance(self, inst_name):
        return self.wbem.GetInstance(inst_name)
    # GetInstance

    def FindInstance(self, inst_name, attr="Name", class_name=None):
        if not class_name:
            class_name = self.typed_class

        if isinstance(inst_name, str) or isinstance(inst_name, unicode):
            _insts = self.EnumerateInstances(class_name)
            return [i for i in _insts if i[attr] == inst_name][0]

        return self.GetInstance(self, inst_name)
    # FindInstance

    def FindInstanceName(self, _name, attr="Name", class_name=None):
        if not class_name:
            class_name = self.typed_class

        _inst_names = self.EnumerateInstanceNames(class_name)
        return [i for i in _inst_names if i[attr] == _name][0]
    # FindInstanceName

    def CreateFilterListInstance(self, name, class_name=None, props={}):
        if not class_name:
            class_name = self.typed_class

        if name:
            props["Name"] = name

        logger.info("Creating Instance of %s", class_name)
        inst = pywbem.CIMInstance(class_name, props)
        return self.wbem.CreateInstance(inst)
    # CreateFilterListInstance

    def DumpWBEMDebug(self):
        logger.info("*** Begin WBEM Debug ***")
        logger.info("  * Last raw request\n'%s'", self.wbem.last_raw_request)
        logger.info("  * Last raw reply\n'%s'", self.wbem.last_raw_reply)

        logger.info("  * Last request\n'%s'", self.wbem.last_request)
        logger.info("  * Last reply\n'%s'", self.wbem.last_reply)
        logger.info("*** End WBEM Debug ***")
    # DumpWBEMDebug
# BaseTestObject


class CIMDomain(object):

    def __init__(self, name, virt, server):
        self.name = name
        self.server = server
        self.virt = virt
        self._domain = get_class(virt)(name)
    #__init__

    def define(self):
        return self._domain.cim_define(self.server)
    # define

    def start(self):
        return self._domain.cim_start(self.server)
    # start

    def shutdown(self):
        return self._domain.cim_shutdown(self.server)
    # shutdown

    def undefine(self):
        return self._domain.undefine(self.server)
    # undefine

    def destroy(self):
        return self._domain.cim_destroy(self.server)
    #destroy
# CIMDomain


class FilterListTest(BaseTestObject):
    cim_basename = "FilterList"

    def __init__(self, server, virt):
        BaseTestObject.__init__(self, server, virt)
    # __init__

    def libvirt_filter_lists(self):
        cmd = "virsh -q -c %s nwfilter-list 2>/dev/null" % self.uri
        ret, filters = run_remote(self.server, cmd)
        if ret:
            logger.error("Error listing existing filters")
            return None

        filters = filters.split("\n")
        l = []
        for f in filters:
            # Append a tuple of (id, name) to list
            t = tuple(a for a in f.strip().split() if a)
            l.append(t)

        return l
    # libvirt_filter_lists

    def cim_filter_lists(self):
        _instances = self.EnumerateInstances()
        l = []
        for i in _instances:
            try:
                # Append a tuple of (id, name) to list
                l.append((i["InstanceId"], i["Name"]))
            except KeyError:
                logger.error("'InstanceID', 'Name' properties not found in Instance %s", i)
                return None

        return l
    # cim_filter_lists

    def id_for_filter_name(self, _list, _name):
        if isinstance(_list[0], tuple):
            return [t[0] for t in _list if t[1] == _name][0]
        elif isinstance(_list[0], CIMInstanceName):
            return self.GetInstance(inst_name)["InstanceID"]
        raise AttributeError("Expecting list of either tuple or CIMInstanceName")
    # id_for_filter_name

    def name_for_filter_id(self, _list, _id):
        if isinstance(_list[0], tuple):
            return [t[1] for t in _list if t[0] == _id][0]
        elif isinstance(_list[0], CIMInstance):
            return [i for i in _list if i["InstanceID"] == _id][0]["Name"]
        raise AttributeError("Expecting list of either tuple or CIMInstance")
    # name_for_filter_id

    def libvirt_filter_dumpxml(self, uuid):
        cmd = "virsh -q -c %s nwfilter-dumpxml %s 2>/dev/null" % (self.uri, uuid)
        ret, out = run_remote(self.server, cmd)
        if ret:
            logger.error("Error executing nwfilter-dumpxml")
            return None

        # Remove all unecessary spaces and new lines
        _xml = "".join([a.strip() for a in out.split("\n") if a])
        return etree.fromstring(_xml)
    # libvirt_filter_dumpxml

    def libvirt_entries_in_filter_lists(self):
        filters = self.libvirt_filter_lists()

        d = {}
        for f in filters:
            root = self.libvirt_filter_dumpxml(f[0])
            if root is None:
                return None

            d[f] = root

        return d
    # libvirt_entries_in_filter_lists

    def cim_entries_in_filter_lists(self):
        d = {}

        _names = self.EnumerateInstanceNames()
        for n in _names:
            l = []
            l.extend(self.Associators(n, result_class="CIM_FilterEntryBase"))
            l.extend(self.Associators(n, assoc_class="KVM_NestedFilterList"))
            d[n] = l

        return d
    # cim_entries_in_filter_lists

    def libvirt_entries_in_filter_list(self, _name, _id=None):
        _id_name = (_id, _name)

        if not _id:
            try:
                _id_name = (self.id_for_filter_name(d.keys(), _name), _name)
            except IndexError:
                return None
        elif not _name:
            try:
                _id_name = (_id, self.name_for_filter_id(d.keys(), _id))
            except IndexError:
                return None

        return self.libvirt_filter_dumpxml(_id_name[0])
    # libvirt_entries_in_filter_list

    def cim_entries_in_filter_list(self, _name, _id=None):
        _inst_name = None

        if not _id:
            try:
                _inst_name = self.GetInstanceName(_name)
            except IndexError:
                return None
        elif not _name:
            try:
                _inst = self.GetInstance(_id, "InstanceID")
                _inst_name = self.GetInstanceName(_inst["Name"])
            except IndexError:
                return None

        return self.Associators(_inst_name, result_class="CIM_FilterEntryBase")
    # cim_entries_in_filter_list

    def libvirt_applied_filter_lists(self, dom_name):
        cmd = "virsh -q -c %s dumpxml %s 2>/dev/null" % (self.uri, dom_name)
        ret, dom_xml = run_remote(self.server, cmd)
        if ret:
            logger.error("Error retrieving domain xml for %s", dom_name)
            return None

        xdoc = etree.fromstring(dom_xml)
        filter_list = xdoc.xpath("/domain/devices/interface/filterref")
        return filter_list
    # libvirt_applied_filter_lists

    def cim_applied_filter_lists(self, dom_name):
        pass
    # cim_applied_filter_lists
# FilterListTest


class FilterRule(object):

    __directions = {"in"   : "1",
                    "out"  : "2",
                    "inout": "3",}

    __versions = {"ip"  : "4",
                  "ipv6": "6",}

    __actions = {"accept"   : "1",
                 "deny"     : "2",
                 "drop"     : "2",
                 "reject"   : "3",
                 "return"   : "4",
                 "continue" : "5",}

    __protocolids = {"ipv4": "2048",
                     "arp" : "2054",
                     "rarp": "32821",
                     "ipv6": "34525",}

    __baserule_map = {"action"      : "Action",
                      "direction"   : "Direction",
                      "priority"    : "Priority",}

    __iprule_map = {"version"     : "HdrIPVersion",
                    ""            : "HdrFlowLabel",
                    "srcipaddr"   : "HdrSrcAddress",
                    "dstipaddr"   : "HdrDestAddress",
                    "srcipmask"   : "HdrSrcMask",
                    "dstipmask"   : "HdrDestMask",
                    "srcipto"     : "HdrSrcAddressEndOfRange",
                    "dstipto"     : "HdrDestAddressEndOfRange",
                    "srcportstart": "HdrSrcPortStart",
                    "dstportstart": "HdrDestPortStart",
                    "srcportend"  : "HdrSrcPortEnd",
                    "dstportend"  : "HdrDestPortEnd",
                    ""            : "HdrDSCP",
                    ""            : "HdrProtocolID",}

    __hdr8021rule_map = {"srcmacaddr": "HdrSrcMACAddr8021",
                         "dstmacaddr": "HdrDestMACAddr8021",
                         "srcmacmask": "HdrSrcMACMask8021",
                         "dstmacmask": "HdrDestMACMask8021",
                         ""          : "HdrPriorityValue8021",
                         ""          : "HdrVLANID8021",
                         "protocolid": "HdrProtocolID8021",}

    ### FIXME Add to proper rule map
    """
                    "": "HealthState",
                    "": "StatusDescriptions",
                    "": "Generation",
                    "": "CommunicationStatus",
                    "": "SystemName",
                    "": "DetailedStatus",
                    "": "Caption",
                    "": "OperationalStatus",
                    "": "SystemCreationClassName",
                    "": "Status",
                    "": "Description",
                    "": "InstallDate",
                    "": "CreationClassName",
                    "": "PrimaryStatus",
                    "": "ElementName",
                    "": "Name",
                    "": "IsNegated",
                    "": "InstanceID",
                    "": "OperatingStatus",
    """

    __basenames = {None  : "FilterEntry",
                   "ip"  : "IPHeadersFilter",
                   "ipv6": "IPHeadersFilter",
                   "tcp" : "IPHeadersFilter",
                   "udp" : "IPHeadersFilter",
                   "igmp": "IPHeadersFilter",
                   "icmp": "IPHeadersFilter",
                   "mac" : "Hdr8021Filter",
                   "arp" : "Hdr8021Filter",
                   "rarp": "Hdr8021Filter",}

    __rulemaps  = {"FilterEntry"    : __baserule_map,
                   "IPHeadersFilter": dict(__baserule_map, **__iprule_map),
                   "Hdr8021Filter"  : dict(__baserule_map, **__hdr8021rule_map),}

    def __init__(self, element):
        self.__dict = element.attrib
        self.__type = None

        for e in element:
            self.__dict = dict(self.__dict, **e.attrib)
            if self.__type is None:
                self.__type = e.tag

        try:
            self.basename = self.__basenames[self.__type]
            self.rulemap = self.__rulemaps[self.basename]
        except KeyError:
            self.basename = None
            self.rulemap = None
    # __init__

    def __getattr__(self, key):
        if key == "direction":
            return self.__directions[self.__dict[key]]
        elif key == "version":
            if self.__type and "ip" in self.__type:
                return self.__versions[self.__type]
        elif key == "action":
            return self.__actions[self.__dict[key]]
        elif key == "type":
            return self.__type
        elif key == "protocolid":
            value = self.__dict[key]
            try:
                return self.__protocolids[value]
            except KeyError:
                return value

        try:
            return self.__dict[key]
        except KeyError:
            return None
    # __getattr__

    def __repr__(self):
        return "FilterRule(type=%s, attributes=%s)" % (self.__type, self.__dict)
    # __repr__

    def __addr_to_list(self, val, base, sep):
        return [long(v, base) for v in val.split(sep)]
    # __addr_to_list

    def __cidr_to_list(self, val):
        int_val = int(val, 10)
        int_val = (0xffffffff >> (32 - int_val)) << (32 - int_val)
        o1 = (int_val & 0xff000000) >> 24
        o2 = (int_val & 0x00ff0000) >> 16
        o3 = (int_val & 0x0000ff00) >> 8
        o4 = int_val & 0x000000ff
        return [o1, o2, o3, o4]
    # __cidr_to_list

    def matches(self, instance):
        # Classname
        if not self.basename or self.basename not in instance.classname:
            return (False, "Classname '%s' does not match instance '%s'" % (self.basename, instance.classname))

        # IP Version
        if self.version:
            prop_name = self.rulemap["version"]
            try:
                inst_version = str(instance[prop_name])
            except KeyError:
                inst_version = None

            if self.version != inst_version:
                return (False, "IP version '%s' does not match instance '%s'" % (self.version, inst_version))

        # Other properties
        for key in self.__dict:
            try:
                inst_key = self.rulemap[key]
            except KeyError:
                inst_key = None

            if not inst_key:
                # logger.info("No match for rule attribute '%s'", key)
                continue

            # convert the property value to string
            prop = instance.properties[inst_key]
            val = self.__getattr__(key)
            if isinstance(val, str) and val.startswith("0x"):
                inst_val = hex(int(prop.value))
            else:
                inst_val = str(prop.value)

            # Handle special cases
            if inst_val != "None":
                # Netmask?
                if "mask" in key:
                    if "." in val:
                        val = self.__addr_to_list(val, base, sep)
                    else:
                        # Assume CIDR
                        val = self.__cidr_to_list(val)
                    inst_val = prop.value
                # Address?
                elif "addr" in key:
                    if val.startswith("$"):
                        # Can't translate address starting with '$'
                        logger.info("Assuming matching address for '%s:%s' and '%s:%s'", key, val, inst_key,inst_val)
                        continue
                    elif prop.is_array and prop.value:
                        sep = "."
                        base = 10
                        if ":" in val:
                            sep = ":"
                            base = 16

                        val = self.__addr_to_list(val, base, sep)
                    inst_val = prop.value
            # if inst_val != None

            if inst_val != val:
                return (False, "Values for '%s':'%s' and '%s':'%s' don't match" % (key, val, inst_key, inst_val))

        return (True, "Found matching CIM Instance: %s" % instance)
    # matches
# FilterRule

