#!/usr/bin/env python

import signal, sys, time 
import ConfigParser
import re

class Parser(object):
    def __init__(self, config_file):
        self.read_config(config_file)
        self.mode=90  # absolute by default
        self.feed_mode=0 #rapid move by default
        self.curr_x=self.curr_y=self.curr_z=0
        self.exp_x=self.exp_y=self.exp_z=0
        self.next_x=self.next_y=self.next_z=0
        default_params=self.params['defaults']
        self.feed_rate=max(default_params['x_feed'], default_params['y_feed'])
        self.feed_rate_z=default_params['z_feed']
        move_params=self.params['move_params']
        self.rapid_feed=(move_params['x_max_feed']**2+move_params['y_max_feed']**2+move_params['z_max_feed']**2)**0.5
        

    def read_config(self, config_file):
        conf = ConfigParser.RawConfigParser()
        conf.read(config_file)
        params={}
        for section in conf.sections():
            params[section]={}
            for option in conf.options(section):
                params[section][option]=conf.getfloat(section,option) 
        self.conf=conf
        self.params=params

############---Setters---############

    def set_mode(self, value):
        self.mode=value

    def set_feed_mode(self, value):
        self.feed_mode=value

    def set_shape(self, value):
        self.shape=value

    def set_clockwise(self, value):
        self.clockwise=value

    def set_coordinates(self, coordinates):
        if 'X' not in coordinates and 'Y' not in coordinates and 'Z' not in coordinates:
            coordinates['X']=0
            coordinates['Y']=0
            coordinates['Z']=0
        if 'X' in coordinates:
            self.exp_x=self.curr_x=self.next_x=coordinates['X']
        if 'Y' in coordinates:
            self.exp_y=self.curr_y=self.next_y=coordinates['Y']
        if 'Z' in coordinates:
            self.exp_z=self.curr_z=self.next_z=coordinates['Z']
###########---Getters---##########

    def open_file(self, fname):
        self.f_handler=open(fname, 'r')

    def read_line(self):
        line = self.f_handler.readline()
        return line

    def convert_line(self, line):
        expr=re.compile(r'([GXYZMSF]-*\d+\.*\d*)')
        instructions={}
        for instr in expr.findall(line.upper()):
            instructions[instr[0]]=float(instr[1:])
        return instructions

    def process(self, instructions):
        if 'G' in instructions:
            if instructions['G'] == 92:         #reset coordintes
                self.set_coordinates(instructions)
            if instructions['G'] in (90,91):
                self.set_mode(instructions['G'])
            if instructions['G'] in (0,1):
                self.set_feed_mode(instructions['G'])
                self.set_shape(1)                 #line
            if instructions['G'] in (2,3):
                self.set_feed_mode(1)
                self.set_shape(2)                # bow
                self.set_clockwise(instructions['G']-2)
        if 'F' in instructions:
            if 'Z' in instructions and 'X' not in instructions and 'Y' not in instructions:
                self.feed_rate_z=instructions['F']
            else:
                self.feed_rate=instructions['F']
        if 'X' in instructions:
            if self.mode==90:
                self.next_x=instructions['X']
            else:
                self.next_x=instructions['X']+self.exp_x
        if 'Y' in instructions:
            if self.mode==90:
                self.next_y=instructions['Y']
            else:
                self.next_y=instructions['Y']+self.exp_y
        if 'Z' in instructions:
            if self.mode==90:
                self.next_z=instructions['Z']
            else:
                self.next_z=instructions['Z']+self.exp_z

    def generate_line_comand(self, dx, dy, dz):
        res={'dir_x':int(dx>0),'dir_y':int(dy>0), 'dir_z':int(dz>0)}
        dx=abs(dx)
        dy=abs(dy)
        dz=abs(dz)
        ds=(dx**2+dy**2+dz**2)**0.5
        move_params=self.params['move_params']
        res['steps_x']=int(dx*move_params['x_steps_per_mm'])
        res['steps_y']=int(dy*move_params['y_steps_per_mm'])
        res['steps_z']=int(dz*move_params['z_steps_per_mm'])
        steps_s=max(res['steps_x'],res['steps_y'],res['steps_z'])
        feed_s=self.feed_rate_z if dx==dy==0 else self.feed_rate
        s_steps_per_mm=steps_s/ds
        interval_s=60/(feed_s*s_steps_per_mm)
        interval_x=0 if dx==0 else 60/(move_params['x_max_feed']*move_params['x_steps_per_mm'])
        interval_y=0 if dx==0 else 60/(move_params['y_max_feed']*move_params['y_steps_per_mm'])
        interval_z=0 if dx==0 else 60/(move_params['z_max_feed']*move_params['z_steps_per_mm'])
        res['interval']=max(interval_s, interval_x, interval_y, interval_z)
        self.exp_x=self.next_x
        self.exp_y=self.next_y
        self.exp_z=self.next_z
        self.curr_x=self.curr_x+res['steps_x']/move_params['x_steps_per_mm']*(res['dir_x']-(not res['dir_x']))
        self.curr_y=self.curr_y+res['steps_y']/move_params['y_steps_per_mm']*(res['dir_y']-(not res['dir_y']))
        self.curr_z=self.curr_z+res['steps_z']/move_params['z_steps_per_mm']*(res['dir_z']-(not res['dir_z']))
        return res

    def is_moved(self):
        return self.next_x-self.exp_x or self.next_y-self.exp_y or self.next_z-self.exp_z

    def get_commands(self):
        while not self.is_moved():
            s=self.read_line()
            if not(s):
                return None
            print self, s
            self.process(self.convert_line(s))
        res=self.generate_line_comand(self.next_x-self.exp_x, self.next_y-self.exp_y, self.next_z-self.exp_z) 
        return res
