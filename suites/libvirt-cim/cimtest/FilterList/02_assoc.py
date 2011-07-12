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
# CIMTest Filter Lists Associators
#

import sys
import helper

from CimTest.ReturnCodes import PASS, FAIL, XFAIL
from CimTest.Globals import logger
from XenKvmLib.const import do_main

sup_types = ["KVM",]

@do_main(sup_types)
def main():
    options = main.options

    _test = helper.FilterListTest(options.ip, options.virt)

    # Fetch current filters with libvirt
    libvirt_filters = _test.libvirt_entries_in_filter_lists()
    if not libvirt_filters:
        return FAIL

    #logger.info("libvirt filters:\n%s", libvirt_filters)

    # Fetch current filters with libvirt-cim
    cim_filters = _test.cim_entries_in_filter_lists()
    if not cim_filters:
        return FAIL

    #logger.info("libvirt-cim filters:\n%s", cim_filters)

    # Compare results
    if len(libvirt_filters) != len(cim_filters):
        logger.error("CIM filters list length and libvirt filters list differ")
        return FAIL

    # Compare each result
    for inst_name in cim_filters:
        _cim_f = _test.GetInstance(inst_name)
        try:
            _key = (_cim_f["InstanceID"], _cim_f["Name"])
            _vir_f = libvirt_filters[_key]
        except KeyError, e:
            logger.error(e)
            return FAIL

        logger.info("")
        logger.info("Processing '%s' filter", _key[1])

        # Check number of rules
        n_vir_rules = len([e for e in _vir_f.getchildren() if e.tag in ["rule", "filterref"]])

        # process each element
        instances = cim_filters[inst_name]
        n_cim_rules = len(instances)

        if n_cim_rules != n_vir_rules:
            logger.error("Number of rules returned by libvirt (%d) and libvirt-cim (%d) differ",
                         n_vir_rules, n_cim_rules)
            return FAIL


        # TODO: Create a new class to handle the filter parsing
        def parse_filter(element, spaces=""):
            logger.info("%s%s(%s)%s",
                        spaces,
                        element.tag,
                        element.attrib and element.attrib or "",
                        element.text and ": %s" % element.text or "")

            # Recurse to last element in tree
            for e in element:
                parse_filter(e, "%s  " % spaces)

            if element.tag == "filterref":
                name = element.get("filter")
                try:
                    i = [inst for inst in instances if inst["Name"] == name][0]
                    logger.info("%s* MATCH: Instance: %s", spaces, i)
                    instances.remove(i)
                    return
                except:
                    raise Exception("No CIM Instance matching this rule was found")
            elif element.tag == "rule":
                if not instances:
                    raise Exception("No CIM Instance matching this rule was found")

                rule = helper.FilterRule(element)

                # Find matching instance
                logger.info("%s* %s", spaces, rule)
                for i in instances:
                    props = ""
                    for p in i.properties.keys():
                        props = "%s '%s':'%s'" % (props, p, i[p])
                    logger.info("%s* %s(%s)", spaces, i.classname, props)

                    matches, msg = rule.matches(i)
                    if msg:
                        logger.info("%s* %s: %s", spaces, matches and "MATCH" or "DON'T MATCH", msg)

                    if matches:
                        instances.remove(i)
                        return

                # No matching instance
                raise Exception("No CIM instance matching rule found")
            else:
                # Unexpected tag, ignore by now
                pass
        # parse_filter

        try:
            parse_filter(_vir_f)
        except Exception, e:
            logger.error("Error parsing filter '%s': %s", _vir_f.tag, e)
            return FAIL

        # Check for leftovers
        for i in instances:
            props = ""
            for p in i.properties.keys():
                props = "%s '%s':'%s'" % (props, p, i[p])

            logger.error("Could NOT find match for instance %s : {%s}", i.classname, props)
            return FAIL
    # end for inst_name in cim_filters

    logger.info("====End of test====")
    return PASS
# main

if __name__ == "__main__":
    sys.exit(main())
