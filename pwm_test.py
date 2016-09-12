#!/usr/bin/env python

import subprocess
import os, signal, sys, time


child=subprocess.Popen('./pwm.py', stdin=subprocess.PIPE)


while True:
    s=raw_input()
    child.stdin.write(s+'\n') 
    child.send_signal(17)
    if s=='STOP':
        exit(0)

for i in range(10):
    time.sleep(1)
