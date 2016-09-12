#!/usr/bin/env python

import os, signal, sys, time

from  PWM_software import PWM

pwm=PWM({})

def sig_handler(signum, frame):
    s=raw_input()
    if s=='STOP':
        pwm.stop()
        print 'STOPPED'
        exit(0)
    duty,direction=s.split()
    pwm.reset_pwm({'duty':int(duty),'direction':int(direction)})
    pwm.run()
    print duty,direction

signal.signal(17, sig_handler)

while True:
    time.sleep(0.5)
