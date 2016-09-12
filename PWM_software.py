#!/usr/bin/env python

import signal, sys, time
from pyA20.gpio import gpio
from pyA20.gpio import port
from pyA20.gpio import connector

min_interval=0.0001
gpio.init()
pwm_port=port.PC4
dir_port=port.PD14
gpio.setcfg(pwm_port, gpio.OUTPUT)
gpio.output(pwm_port, 0)
gpio.setcfg(dir_port, gpio.OUTPUT)
gpio.output(dir_port, 1)

class PWM(object):
    def __init__(self, params):
        if params:
            self.reset_pwm(params)
        self._stop=1
        signal.signal(signal.SIGALRM, self.alarm_handler)

    def reset_pwm(self, params):
        duty=params['duty']
        self.direction=params['direction']
        if duty<50:
            self.up_time=min_interval
            self.down_time=min_interval/duty*(100-duty)
        else:
            self.down_time=min_interval
            self.up_time=min_interval/(100-duty)*duty
        gpio.output(dir_port, self.direction)
        print self.up_time, self.down_time
            

    def run(self):
        self._stop=0
        self.pwm_value=1
        gpio.output(pwm_port, 1)
        gpio.output(dir_port, self.direction)
        signal.setitimer(signal.ITIMER_REAL, self.up_time)

    def alarm_handler(self, signum, frame):
        set_time=self.down_time if self.pwm_value else self.up_time 
        self.pwm_value = 1 - self.pwm_value 
        gpio.output(pwm_port, self.pwm_value)
        signal.setitimer(signal.ITIMER_REAL, set_time)

    def stop(self):
        self._stop=1
        self.pwm_value=0
        signal.setitimer(signal.ITIMER_REAL, 0)
        gpio.output(pwm_port, 0)
        gpio.output(dir_port, 1)
        
