#
# Copyright 2008 IBM Corp. 
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
#    Deepti B. Kalakeri <dkalaker@in.ibm.com>
#    Guolian Yun <yunguol@cn.ibm.com>
#    Kaitlin Rupert <karupert@us.ibm.com>
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
import logging
import traceback

global CIM_USER
global CIM_PASS
global CIM_NS
global CIM_LEVEL
global CIM_FUUID
global CIM_IP
global CIM_PORT

global CIM_ERROR_ASSOCIATORNAMES
global CIM_ERROR_ENUMERATE
global CIM_ERROR_GETINSTANCE

CIM_USER  = os.getenv("CIM_USER")
CIM_PASS  = os.getenv("CIM_PASS")
CIM_NS    = os.getenv("CIM_NS")
CIM_LEVEL = os.getenv("CIM_LEVEL")
CIM_FUUID = os.getenv("CIM_FUUID")
CIM_TC    = os.getenv("CIM_TC")
CIM_IP    = os.getenv("CIM_IP")
CIM_PORT = "5988"
NM = "TEST LOG"
logging.basicConfig(filename='/dev/null')
logger = logging.getLogger(NM)
logging.PRINT = logging.DEBUG + 50
logging.addLevelName(logging.PRINT, "PRINT")


CIM_ERROR_ENUMERATE        = "Failed to enumerate the class of %s"
CIM_ERROR_GETINSTANCE      = "Failed to get instance by the class of %s"
CIM_ERROR_ASSOCIATORS      = "Failed to get associators information for %s"
CIM_ERROR_ASSOCIATORNAMES  = "Failed to get associatornames according to %s"

if not CIM_NS:
    CIM_NS = "root/cimv2"

if not CIM_LEVEL:
    CIM_LEVEL=logging.PRINT
else:
    CIM_LEVEL = os.getenv("CIM_LEVEL")

if not CIM_FUUID:
    CIM_FUUID = "/tmp/cimtest.uuid"

if not CIM_TC:
    CIM_TC = " " 
if not CIM_IP:
    CIM_IP = "localhost"


def log_param(log_level=logging.ERROR, file_name="cimtest.log"):
    logger.setLevel(logging.DEBUG)
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    #create file handler and set level to debug
    fh = logging.FileHandler(file_name)
    fh.setLevel(logging.DEBUG)
    #create formatter
    formatter = logging.Formatter(\
                        "%(asctime)s:%(name)s:%(levelname)s   \t-  %(message)s",
                        datefmt="%a, %d %b %Y %H:%M:%S")
    #add formatter to handlers
    fh.setFormatter(formatter)
    formatter = logging.Formatter("%(levelname)s \t- %(message)s")
    ch.setFormatter(formatter)
    #add handlers to logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    #Print header
    logger.info("====%s Log====", CIM_TC)

def log_bug(bug_num):
    logger.info("Known Bug:%s" % bug_num)
    print "Bug:<%s>" % bug_num

