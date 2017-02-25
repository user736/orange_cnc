#!/usr/bin/env python

import signal, sys, time
from pyA20.gpio import gpio
from pyA20.gpio import port

class Stepper(object):

    def __init__(self, params):

        self.value=0
        self.steps_pin = params['steps_pin'] if 'steps_pin' in params else 1
        self.dir_pin = params['dir_pin'] if 'dir_pin' in params else 2
        self.steps = params['steps'] if 'steps' in params else 0
        self.dir = params['dir'] if 'dir' in params else 0
        self.interval = params['interval'] if 'interval' in params else 0.05
        self.steps2sync = params['steps2sync'] if 'steps2sync' in params else 100
        self.stop=1
        if self.steps:
            self.buzy=1

        signal.signal(signal.SIGALRM, self.alarm_handler)

        gpio.init()
        gpio.setcfg(self.steps_pin, gpio.OUTPUT)
        gpio.setcfg(self.dir_pin, gpio.OUTPUT)
        gpio.output(self.steps_pin, 0)
        gpio.output(self.dir_pin, 0)


    def reset_params(self, params):

        if 'steps' in params:
            self.steps = params['steps']
        if 'dir' in params:
            self.dir = params['dir']
        if 'interval' in params:
            self.interval = params['interval']
        if 'steps2sync' in params:
            self.steps2sync = params['steps2sync']


    def alarm_handler(self, signum, frame):

        if self.s2s>0 and self.steps>0:
            self.value=1-self.value
            if self.value==0:
                self.s2s-=1
                self.steps-=1
            gpio.output(self.steps_pin, self.value)
        else:
            signal.setitimer(signal.ITIMER_REAL, 0)
            self.stop=1
            if self.steps==0:
                self.buzy=0


    def run(self):

        self.buzy=1
        self.stop=0
        self.s2s=self.steps2sync
        signal.setitimer(signal.ITIMER_REAL, self.interval, self.interval)

