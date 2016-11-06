#!/usr/bin/env python

# Workaround for exception: "AttributeError: 'module' object has no attribute 'PA4'" in module pyA20.gpio

import os
import sys
import mmap
import struct

def config():   #config PA4 as GPIO out

    f = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
    pin_mem = mmap.mmap(f, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=0x01C20000)
    pin_mem.seek(0x800,0)
    data=(struct.unpack('I', pin_mem.read(4))[0])
    data = data | (0b0001 << 16)
    data = data & ~(0b0011 << 17)
    pin_mem.seek(0x800,0)
    pin_mem.write(struct.pack('I', data))

def set(value):

    f = os.open('/dev/mem', os.O_RDWR | os.O_SYNC)
    pin_mem = mmap.mmap(f, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=0x01C20000)
    pin_mem.seek(0x810,0)
    data=(struct.unpack('I', pin_mem.read(4))[0])

    if value:
        data = data | (0b0001 << 4)
    else:
        data = data & ~(0b0001 << 4)

    pin_mem.seek(0x810,0)
    pin_mem.write(struct.pack('I', data))

config()
set(1)
