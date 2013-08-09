#!/bin/bash

# Copyright 2008 IBM Corp.
# Author: Dan Smith <danms@us.ibm.com>
#
# Create an x86-bootable disk image from an initramfs image
#
# Usage:
#
#  ./xmt-makefv <initramfs> <imagename>
#
# Requires: kpartx, parted, tune2fs, mkinitrd, grub

PARTED="parted -s"
TMPMOUNT=/tmp/cimtest_image_temp
SIZE=16
QEMU_VER=082
QEMU_FILE=""
DUMMY_PATH="cimtest-dummy-image"

if [ -e "/usr/lib64/xen/bin/qemu-dm" ]; then
    QEMU_FILE="/usr/lib64/xen/bin/qemu-dm"
elif [ -e "/usr/lib/xen/bin/qemu-dm" ]; then
    QEMU_FILE="/usr/lib/xen/bin/qemu-dm"
fi

if [ -z $QEMU_FILE ]; then
    CUR_QEMU_VER=0
else
    CUR_QEMU_VER=`strings $QEMU_FILE | awk '/version [0-9]/ { print $5; }' | sed 's/,//' | sed 's/\.//g'`
fi

die() {
    echo "FAILED: $1" >&2
 
    umount $TMPMOUT >/dev/null 2>&1
    kpartx -d $loop >/dev/null 2>&1
    losetup -d $loop >/dev/null 2>&1

    exit 1
}

make_empty() {
    local size=$1
    local file=$2

    dd if=/dev/zero of=$file bs=1M count=$size >/dev/null 2>&1
}

partition() {
    local file=$1

    $PARTED $file mklabel msdos
    $PARTED $file mkpart primary ext2 0 $(($SIZE - 1))
}

mount_partition() {
    local file=$1
    local loopdev=$(losetup -f | awk -F / '{print $NF}')

    mkdir -p $TMPMOUNT || die "Failed to create temp: $TMPMOUNT"

    losetup /dev/$loopdev $file || die "Failed to losetup $file"
    kpartx -a /dev/$loopdev || die "Failed to kpartx $loopdev"
    sleep 2
    mke2fs -t ext2 /dev/mapper/${loopdev}p1 >/dev/null 2>&1 || die "Failed to mkfs ${loopdev}p1"
    tune2fs -j /dev/mapper/${loopdev}p1 >/dev/null 2>&1|| die "Failed to add journal"
    sleep 2
    mount /dev/mapper/${loopdev}p1 $TMPMOUNT || die "Failed to mount ${loopdev}p1"

    echo $loopdev 
}

unmount_partition() {
    local loopdev=$1

    umount $TMPMOUNT || die "Failed to unmount $TMPMOUNT"
    kpartx -d /dev/$loopdev || die "Failed to un-kpartx $loopdev"
    losetup -d /dev/$loopdev || die "Failed to delete loop $loopdev"
}

copy_in_ramdisk() {
    local target=$1
    local ramdisk=$2

    zcat $ramdisk | (cd $target && cpio -id >/dev/null 2>&1)
}

kernel_path() {
    local prefix=$1

    local image=`find /boot | grep vmlinuz | egrep -v 'xen|hmac|rescue' | tail -n1`

    if [ -z $image ]; then
        touch /boot/vmlinuz-$DUMMY_PATH
        mkdir /lib/modules/$DUMMY_PATH
        image="/boot/vmlinuz-$DUMMY_PATH"
    fi

    echo $image
}

copy_in_kernel() {
    local target=$1
    local kernel=$(kernel_path)

    [ -f "$kernel" ] || die "Unable to find a kernel"

    local ver=$(echo $kernel | awk -F 'vmlinuz-' '{print $2}')

    [ -d /lib/modules/$ver ] || die "No kver $ver"

    cp $kernel ${target}/vmlinuz

    mkinitrd  --preload ata_piix ${target}/initrd $ver
 
    if [ $ver == $DUMMY_PATH ]; then
        echo "No non-Xen kernel found.  Using a fake image."
        rm /boot/vmlinuz-$DUMMY_PATH
        rm -rf /lib/modules/$DUMMY_PATH
    fi
}

grub_image() {
    local root=$1
    local file=$2

    mkdir ${root}/grub
    cp /boot/grub/stage? /boot/grub/e2fs_stage1_5 ${root}/grub

    cat >tmp_grub <<EOF
device (hd0) $file
root (hd0,0)
setup (hd0)
EOF

    grub < tmp_grub >grub.log 2>&1
    rm tmp_grub

cat >${root}/grub/grub.conf <<EOF
default 0
timeout 1
title Test Environment
    root (hd0,0)
EOF

if [ $CUR_QEMU_VER -lt $QEMU_VER ]; then
    cat >>${root}/grub/grub.conf <<EOF
    kernel /vmlinuz root=/dev/hda1
    initrd /initrd
EOF
else
    cat >>${root}/grub/grub.conf <<EOF
    kernel /vmlinuz root=/dev/sda1
    initrd /initrd
EOF
fi
}

ramdisk=$1
output=$2

make_empty $SIZE $output
partition $output
loop=$(mount_partition $output)

(losetup /dev/$loop >/dev/null 2>&1) || die "Failed to mount image"

copy_in_ramdisk $TMPMOUNT $ramdisk
copy_in_kernel $TMPMOUNT
grub_image $TMPMOUNT $output
unmount_partition $loop
