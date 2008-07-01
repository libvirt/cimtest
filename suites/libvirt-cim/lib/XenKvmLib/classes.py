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
#

virt_types = ['Xen', 'KVM', 'XenFV', 'LXC']

def get_typed_class(virt, basename):
    if virt not in virt_types:
        if virt != "Virt" and basename != "MigrationJob":
            raise ValueError('Invalid class type')

    if basename == None or basename == '':
        raise ValueError('Invalide class base name')

    if virt == 'XenFV':
        virt = 'Xen'

    return '%s_%s' % (virt, basename)

def get_class_type(cn):
    dash_index = cn.find('_')
    if dash_index <= 0:
        raise ValueError('No type in class name')

    return cn[:dash_index]

def get_class_basename(cn):
    dash_index = cn.find('_')
    if dash_index <= 0 or dash_index >= len(cn):
        raise ValueError('No type prefix in class name')

    return cn[dash_index+1:]

