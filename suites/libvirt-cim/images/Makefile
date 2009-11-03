#
# Copyright 2008 IBM Corp.
#
# Authors:
#    Dan Smith <danms@us.ibm.com>
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
DEFAULT_IMG_LOC = /var/lib/libvirt/images

DEFAULT_KERNEL = $(DEFAULT_IMG_LOC)/default-xen-kernel
DEFAULT_INITRD = $(DEFAULT_IMG_LOC)/default-xen-initrd
DEFAULT_DIMAGE = $(DEFAULT_IMG_LOC)/default-xen-dimage
DEFAULT_KVMIMG = $(DEFAULT_IMG_LOC)/default-kvm-dimage

DEFAULT_LXCINIT = $(DEFAULT_IMG_LOC)/cimtest_lxc_init
DEFAULT_LXC_MNT_DIR = $(DEFAULT_IMG_LOC)/lxc_files

SECONDARY_DIMAGE = $(DEFAULT_DIMAGE).2ND
SECONDARY_KVMIMG = $(DEFAULT_KVMIMG).2ND

XMT_BASE = xm-test
XMT_DIMAGE = $(XMT_BASE)/xmt_disk.img
XMT_INITRD = $(XMT_BASE)/initrd-1.1-i386.img
XMT_IRAMFS = $(XMT_BASE)/xm-test.gz
XMT_URL=http://xm-test.xensource.com/ramdisks/initrd-1.1-i386.img

# Default to xm-test ramdisk image & kvm image for now
default: xmtestimage $(DEFAULT_KERNEL) $(DEFAULT_KVMIMG) $(DEFAULT_LXCINIT) \
         $(DEFAULT_LXC_MNT_DIR)

$(DEFAULT_KERNEL):
	if uname -r | grep -q xen; then \
		cp /boot/vmlinuz-`uname -r` $@; \
	fi

$(XMT_INITRD):
	mkdir -p $(XMT_BASE)
	(cd $(XMT_BASE) && wget $(XMT_URL))

$(XMT_DIMAGE): $(XMT_IRAMFS)
	chmod +x xmt-makefv.sh
	./xmt-makefv.sh $(XMT_IRAMFS) $(XMT_DIMAGE)

$(XMT_IRAMFS): $(XMT_INITRD)
	chmod +x xmt-convert.sh
	(cd $(XMT_BASE) && sh ../xmt-convert.sh `basename $(XMT_INITRD)`)

xmtestimage: $(XMT_IRAMFS) $(DEFAULT_KERNEL) $(XMT_DIMAGE)
	cp $(XMT_IRAMFS) $(DEFAULT_INITRD)
	cp $(XMT_DIMAGE) $(DEFAULT_DIMAGE)
	cp $(XMT_DIMAGE) $(SECONDARY_DIMAGE)

$(DEFAULT_KVMIMG):
	# Use an empty disk temporarily
	cp $(XMT_DIMAGE) $(DEFAULT_KVMIMG)
	cp $(XMT_DIMAGE) $(SECONDARY_KVMIMG)

$(DEFAULT_LXCINIT):
	echo  "exec /bin/bash" > $(DEFAULT_LXCINIT)
	chmod 755 $(DEFAULT_LXCINIT)

$(DEFAULT_LXC_MNT_DIR):
	mkdir $(DEFAULT_IMG_LOC)/lxc_files

clean:
	rm -f $(DEFAULT_KERNEL) $(DEFAULT_INITRD) $(DEFAULT_DIMAGE) $(SECONDARY_DIMAGE) 
	rm -f $(DEFAULT_KVMIMG) $(SECONDARY_KVMIMG)
	rm -rf $(DEFAULT_LXCINIT) $(DEFAULT_LXC_MNT_DIR)
	rm -Rf $(XMT_BASE)
