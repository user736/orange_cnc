#!/usr/bin/env python

import signal, sys, time
from pyA20.gpio import gpio
from pyA20.gpio import port
from pyA20.gpio import connector

class Movement_handler(object):

    def __init__(self, params):
        self.params=params
        self.buzy=0
        self.move_resul={'success':1, 'dx':0, 'dy':0, 'dz':0}
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

        self.reset_movement({})

    def reset_movement(self, movement):
        if not self.buzy and self.params['debug']>1:
            print 'input >', movement
        movement['value']=0
        movement['c_x']=0
        movement['c_y']=0
        movement['c_z']=0
        if 'steps_x' not in movement:
            movement['steps_x']=0
        if 'steps_y' not in movement:
            movement['steps_y']=0
        if 'steps_z' not in movement:
            movement['steps_z']=0
        if 'exp_x' not in movement:
            movement['exp_x']=movement['steps_x']
        if 'exp_y' not in movement:
            movement['exp_y']=movement['steps_y']
        if 'exp_z' not in movement:
            movement['exp_z']=movement['steps_z']
        if 'dir_x' not in movement:
            movement['dir_x']=0
        if 'dir_y' not in movement:
            movement['dir_y']=0
        if 'dir_z' not in movement:
            movement['dir_z']=0
        if 'interval' not in movement:
            movement['interval']=0.01
        movement['max_steps']= max(movement['steps_x'], movement['steps_y'], movement['steps_z'])
        if not movement['max_steps']:
            movement['max_steps']=1
        movement['s_x']= 0 if movement['steps_x'] and (movement['steps_x']==movement['max_steps'] or movement['max_steps']//movement['steps_x']>1) else 1
        #movement['q_x']= movement['max_steps']//movement['steps_x'] if not(movement['s_x']) else movement['max_steps']//(movement['max_steps'] - movement['steps_x'])
        movement['q_x']= round(movement['max_steps']/movement['steps_x']) if not(movement['s_x']) else round(movement['max_steps']/(movement['max_steps'] - movement['steps_x']))
        movement['s_y']= 0 if movement['steps_y'] and (movement['steps_y']==movement['max_steps'] or movement['max_steps']//movement['steps_y']>1) else 1
        #movement['q_y']= movement['max_steps']//movement['steps_y'] if not(movement['s_y']) else movement['max_steps']//(movement['max_steps'] - movement['steps_y'])
        movement['q_y']= round(movement['max_steps']/movement['steps_y']) if not(movement['s_y']) else round(movement['max_steps']/(movement['max_steps'] - movement['steps_y']))
        movement['s_z']= 0 if movement['steps_z'] and (movement['steps_z']==movement['max_steps'] or movement['max_steps']//movement['steps_z']>1) else 1
        #movement['q_z']= movement['max_steps']//movement['steps_z'] if not(movement['s_z']) else movement['max_steps']//(movement['max_steps'] - movement['steps_z'])
        movement['q_z']= round(movement['max_steps']/movement['steps_z']) if not(movement['s_z']) else round(movement['max_steps']/(movement['max_steps'] - movement['steps_z']))
        self.movement=movement
        gpio.output(port.PA8, movement['dir_x'])
        gpio.output(port.PA7, movement['dir_y'])
        gpio.output(port.PA19, movement['dir_z'])
        if self.params['debug']>1:
            print movement

    def alarm_handler(self, signum, frame):
        movement=self.movement
        if 'steps_x' not in movement \
        or 'steps_y' not in movement \
        or 'steps_z' not in movement \
        or movement['steps_x']+movement['steps_y']+movement['steps_z']==0 or self.stop:
            self.buzy=0
            move_params=self.params['move_params']
            dx=(movement['exp_x']-movement['steps_x'])/move_params['x_steps_per_mm']
            dy=(movement['exp_y']-movement['steps_y'])/move_params['y_steps_per_mm']
            dz=(movement['exp_z']-movement['steps_z'])/move_params['z_steps_per_mm']
            self.move_resul={'success':not (movement['steps_x']+movement['steps_y']+movement['steps_z']), 'dx':dx, 'dy':dy, 'dz':dz}
            signal.setitimer(signal.ITIMER_REAL, 0)
        else:
            movement['value']=1-movement['value']
            if movement['steps_x'] > 0:
                if (movement['c_x']==movement['q_x']-1)^(movement['s_x']):
                    gpio.output(port.PA20, movement['value'])
                    if not(movement['value']):
                        movement['steps_x']-=1
            if movement['steps_y'] > 0:
                if (movement['c_y']==movement['q_y']-1)^(movement['s_y']):
                    gpio.output(port.PA10, movement['value'])
                    if not(movement['value']):
                        movement['steps_y']-=1
            if movement['steps_z'] > 0:
                if (movement['c_z']==movement['q_z']-1)^(movement['s_z']):
                    gpio.output(port.PA9, movement['value'])
                    if not(movement['value']):
                        movement['steps_z']-=1
            if not(movement['value']):
                movement['c_x']+=1
                if movement['c_x']==movement['q_x']:
                    movement['c_x']=0
                movement['c_y']+=1
                if movement['c_y']==movement['q_y']:
                    movement['c_y']=0
                movement['c_z']+=1
                if movement['c_z']==movement['q_z']:
                    movement['c_z']=0
                if (movement['s_x'] and movement['q_x']==2 and not movement['c_x']) \
                or (movement['s_y'] and movement['q_y']==2 and not movement['c_y']) \
                or (movement['s_z'] and movement['q_z']==2 and not movement['c_z']):
                    self.reset_movement(self.movement)

    def run(self):
        self.buzy=1
        self.stop=0
        signal.setitimer(signal.ITIMER_REAL, self.movement['interval'], self.movement['interval'])

    def get_movement(self):
        return self.movement

    def break_movement(self):
        self.stop=1

    def get_move_res(self):
        return self.move_resul

    def is_buzy(self):
        return self.buzy
