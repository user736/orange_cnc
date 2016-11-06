#!/usr/bin/env python

import pwm_hard
import PA4

class Spindle(object):

    def __init__(self, conf):
        self.pwm=pwm_hard.PWM()
        if "max_duty" not in conf or "max_rpm" not in conf:
            exit("max_duty & max_rpm is mandatory conf parameters") 
        self.conf=conf
        PA4.set(1)

    def run(self, rpm):
        conf=self.conf
        duty = max(rpm > 0, int((conf["max_duty"]*rpm)//conf["max_rpm"]))
        self.pwm.set_duty(duty)
        self.pwm.run()
        PA4.set(0)

    def stop(self):
        self.pwm.stop()
        PA4.set(1)
