#!/usr/bin/env python

import signal, sys, time
from pyA20.gpio import gpio
from pyA20.gpio import port
from pyA20.gpio import connector

class Movement_handler(object):

    def __init__(self, params):
        self.buzy=0
        signal.signal(signal.SIGALRM, self.alarm_handler)

        gpio.init() #Initialize module. Always called first

        gpio.setcfg(port.PA10, gpio.OUTPUT) 
        gpio.setcfg(port.PA20, gpio.OUTPUT)    
        gpio.setcfg(port.PA9, gpio.OUTPUT)
        gpio.setcfg(port.PA8, gpio.OUTPUT)
        gpio.setcfg(port.PA7, gpio.OUTPUT)
        gpio.setcfg(port.PA19, gpio.OUTPUT)
        gpio.output(port.PA10, 0)
        gpio.output(port.PA20, 0)
        gpio.output(port.PA9, 0)
        gpio.output(port.PA8, 0)
        gpio.output(port.PA7, 0)
        gpio.output(port.PA19, 0)

        self.reset_params(params)

    def reset_params(self, params):
        params['value']=0
        params['c_x']=0
        params['c_y']=0
        params['c_z']=0
        if 'steps_x' not in params:
            params['steps_x']=0
        if 'steps_y' not in params:
            params['steps_y']=0
        if 'steps_z' not in params:
            params['steps_z']=0
        if 'dir_x' not in params:
            params['dir_x']=0
        if 'dir_y' not in params:
            params['dir_y']=0
        if 'dir_z' not in params:
            params['dir_z']=0
        if 'interval' not in params:
            params['interval']=0.01
        params['max_steps']= max(params['steps_x'], params['steps_y'], params['steps_z'])
        if not params['max_steps']:
            params['max_steps']=1
        params['s_x']= 0 if params['steps_x'] and (params['steps_x']==params['max_steps'] or params['max_steps']//params['steps_x']>1) else 1
        params['q_x']= params['max_steps']//params['steps_x'] if not(params['s_x']) else params['max_steps']//(params['max_steps'] - params['steps_x'])
        params['s_y']= 0 if params['steps_y'] and (params['steps_y']==params['max_steps'] or params['max_steps']//params['steps_y']>1) else 1
        params['q_y']= params['max_steps']//params['steps_y'] if not(params['s_y']) else params['max_steps']//(params['max_steps'] - params['steps_y'])
        params['s_z']= 0 if params['steps_z'] and (params['steps_z']==params['max_steps'] or params['max_steps']//params['steps_z']>1) else 1
        params['q_z']= params['max_steps']//params['steps_z'] if not(params['s_z']) else params['max_steps']//(params['max_steps'] - params['steps_z'])
        self.params=params
        gpio.output(port.PA8, params['dir_x'])
        gpio.output(port.PA7, params['dir_y'])
        gpio.output(port.PA19, params['dir_z'])
        print params

    def alarm_handler(self, signum, frame):
        params=self.params
        if 'steps_x' not in params \
        or 'steps_y' not in params \
        or 'steps_z' not in params \
        or params['steps_x']+params['steps_y']+params['steps_z']==0:
            signal.setitimer(signal.ITIMER_REAL, 0)
            self.buzy=0
        else:
            params['value']=1-params['value']
            if params['steps_x'] > 0:
                if (params['c_x']==params['q_x']-1)^(params['s_x']):
                    gpio.output(port.PA20, params['value'])
                    if not(params['value']):
                        params['steps_x']-=1
            if params['steps_y'] > 0:
                if (params['c_y']==params['q_y']-1)^(params['s_y']):
                    gpio.output(port.PA10, params['value'])
                    if not(params['value']):
                        params['steps_y']-=1
            if params['steps_z'] > 0:
                if (params['c_z']==params['q_z']-1)^(params['s_z']):
                    gpio.output(port.PA9, params['value'])
                    if not(params['value']):
                        params['steps_z']-=1
            if not(params['value']):
                params['c_x']+=1
                if params['c_x']==params['q_x']:
                    params['c_x']=0
                params['c_y']+=1
                if params['c_y']==params['q_y']:
                    params['c_y']=0
                params['c_z']+=1
                if params['c_z']==params['q_z']:
                    params['c_z']=0
                if (params['s_x'] and params['q_x']==2) or (params['s_y'] and params['q_y']==2) or (params['s_z'] and params['q_z']==2):
                    self.reset_params(self.params)

    def run(self):
        self.buzy=1
        signal.setitimer(signal.ITIMER_REAL, self.params['interval'], self.params['interval'])

    def is_buzy(self):
        return self.buzy
