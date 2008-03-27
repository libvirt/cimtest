#
# Copyright 2008 IBM Corp. 
#
# Authors:
#     Murillo F. Bernardes <mfb@br.ibm.com>
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

class _Method:
    def __init__(self, invoker, name):
        self.__invoker = invoker 
        self.__name = name

    def __getattr__(self, name):
        return _Method(self.__invoker, "%s.%s" % (self.__name, name))

    def __call__(self, **args):
        return self.__invoker(self.__name, args)



class CIMMethodClass:

    def __init__(self, conn, inst_name):
        self.conn = conn
        self.inst = inst_name

    def __invoke(self, method, params):
        try:
            return self.conn.InvokeMethod(method, self.inst, **params)
        except pywbem.CIMError, arg:
            print 'InvokeMethod(%s): %s' % (method, arg[1])
            raise

    def __getattr__(self, name):
        # magic method dispatcher
        return _Method(self.__invoke, name)

#
#

class CIMClassMOF:

    __supported_types = [int, str, bool]

    def __init__(self, attrs = None):
        """attrs should be dict
        """

        if attrs != None:
            self.__dict__.update(attrs)

    def mof(self):
        """mof()

        Return value is a string, containing the mof representation of the 
        object.

        Attribute types supported are : int, str, bool.

        Attributes with unsupported types will be silently ignored when 
        converting to mof representation.
        """

        mof_str = "instance of " + self.__class__.__name__ + " {\n"
        for key, value in self.__dict__.items():
            value_type = type(value)
            if value_type not in self.__supported_types:
                continue

            mof_str += "%s = " % key
            if value_type == int:
                mof_str += "%d" % value
            elif value_type == bool:
                mof_str += str(value).lower()
            else:
                mof_str += '"%s"' % value
            mof_str += ";\n"

        mof_str += "};"
        return mof_str

    def __str__(self):
        return self.mof()


