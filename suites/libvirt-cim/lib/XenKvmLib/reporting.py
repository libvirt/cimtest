#
# Copyright 2008 IBM Corp.
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

import os
import sys
import commands
import smtplib
from time import gmtime, strftime
from VirtLib import utils
from XenKvmLib.const import get_provider_version 

def get_cmd_val(cmd, ip):
    rc, out = utils.run_remote(ip, cmd)
    if rc != 0:
        return "Unknown"
    return out

def get_cimtest_version():
    revision = commands.getoutput("hg parents --template \
    \"{rev}\" 2>/dev/null")
    changeset = commands.getoutput("hg parents --template \
    \"{node|short}\" 2>/dev/null")
    return revision, changeset

def get_libvirt_ver(ip):
    libvirt_ver = "Unknown"
    hyp_ver = "Unknown"
    cmd = "virsh version"
    virsh_ver = get_cmd_val(cmd, ip)
    if virsh_ver != "Unknown":
        if len(virsh_ver.splitlines()) == 4:
            if virsh_ver.splitlines()[0].find("libvir"):
                libvirt_ver = virsh_ver.splitlines()[0].split()[4]

            if virsh_ver.splitlines()[3].find("hypervisor"):
                hyp_ver = virsh_ver.splitlines()[3].split("hypervisor")[1]
                hyp_ver = hyp_ver.split(": ")[1]

    return libvirt_ver, hyp_ver


def get_cimom_ver(ip):
    cimom = get_cmd_val("ps -ef | grep cimserver | grep -v grep", ip)
    if cimom != "Unknown":
        cimom = "Pegasus"
    else:
        cimom = get_cmd_val("ps -ef | grep sfcb | grep -v grep", ip)
        if cimom != "Unknown":
            cimom = "sfcb"

    if cimom == "Pegasus":
        cimom_ver = get_cmd_val("cimserver -v", ip)
    elif cimom == "sfcb":
        cimom_ver = get_cmd_val("sfcbd -v", ip)
    else:
        cimom_ver = "unknown version"

    return cimom, cimom_ver


def get_env_data(ip, virt):
    distro = get_cmd_val("cat /etc/issue | awk 'NR<=1'", ip)
    kernel_ver = get_cmd_val("uname -r", ip)

    libvirt_ver, hyp_ver = get_libvirt_ver(ip)

    cimom, cimom_ver = get_cimom_ver(ip)

    env = "Distro: %s\nKernel: %s\nlibvirt: %s\nHypervisor: %s\nCIMOM: %s %s\n"\
          % (distro, kernel_ver, libvirt_ver, hyp_ver, cimom, cimom_ver)

    rev, changeset = get_provider_version(virt, ip)
    cimtest_revision, cimtest_changeset = get_cimtest_version()

    lc_ver = "Libvirt-cim revision: %s\nLibvirt-cim changeset: %s\n" % \
             (rev, changeset)
    cimtest_ver = "Cimtest revision: %s\nCimtest changeset: %s\n" % \
                  (cimtest_revision, cimtest_changeset)

    return env + lc_ver + cimtest_ver, distro

def parse_run_output(log_file):
    rvals = { 'PASS' : 0,
              'FAIL' : 0,
              'XFAIL' : 0,
              'SKIP' : 0,
            }

    tstr = { 'PASS' : "",
             'FAIL' : "",
             'XFAIL' : "",
             'SKIP' : "",
           }

    fd = open(log_file, "r")

    run_output = ""
    for line in fd.xreadlines():
        for type, val in rvals.iteritems():
            if type in line:
                if type == "FAIL" and "py: FAIL" not in line:
                    continue
                rvals[type] += 1
                tstr[type] += "%s" % line
        run_output += line

    fd.close()

    return rvals, tstr, run_output

def build_report_body(rvals, tstr, div):
    results = ""
    test_total = 0
    for type, val in rvals.iteritems():
        results += " %-10s: %d\n" % (type, val)
        test_total += val

    results_total  = " -----------------\n %-10s: %d\n" % ("Total", test_total)

    test_block = ""
    for type, str in tstr.iteritems():
        if type == "PASS" or str == "":
            continue
        test_block += "%s Test Summary:\n%s\n%s" % (type, str, div)

    return results, results_total, test_block

def gen_report(virt, ip, log_file):
    date = strftime("%b %d %Y", gmtime())

    cimom, cimom_ver = get_cimom_ver(ip)

    sys_env, distro = get_env_data(ip, virt)

    heading  = "Test Run Summary (%s): %s on %s with %s" % (date, virt, 
                                                            distro, cimom)

    divider = "=================================================\n"

    rvals, tstr, run_output = parse_run_output(log_file)

    res, res_total, test_block = build_report_body(rvals, tstr, divider)

    report = divider + heading + "\n" + divider + sys_env + divider + res \
             + res_total + divider + test_block + "Full report:\n" \
             + run_output

    fd = open(log_file, "w")
    rc = fd.write(report)
    if rc is not None:
        print "Error %s writing report to: %s." % (rc, log_file)
    fd.close()

    return report, heading


def send_report(to_addr, from_addr, relay, report, heading):
    headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (from_addr, to_addr,
              heading)

    message = headers + report

    try:
        server = smtplib.SMTP(relay)
        result = server.sendmail(from_addr, to_addr, message)
        server.quit()

        if result:
            for recip in result.keys():
                print "Could not deliver mail to: %s" % recip

    except Exception, details:
        print "Encountered a problem mailing report: %s" % details

