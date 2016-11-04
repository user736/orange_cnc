#!/usr/bin/env python

import pwm_hard

class PWM(object):

    def __init__(self, conf):
        self.pwm=pwm_hard.PWM()
        if "max_duty" not in conf or "max_rpm" not in conf:
            exit("max_duty & max_rpm is mandatory conf parameters") 
        self.conf=conf

    def run(self, rpm):
        conf=self.conf
        duty = max(rpm > 0, int((conf["max_duty"]*rpm)//conf["max_rpm"]))
        self.pwm.set_duty(duty)
        self.pwm.run()

    def stop(self):
        self.pwm.stop()


