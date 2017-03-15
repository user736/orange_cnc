#!/usr/bin/env python

import signal, sys
from time import sleep
from Conf import conf_parser
from  S_handler import Steppers_handler
import G_parser
import subprocess, threading
import Spindle
from pygame_handler import *
from joystick import *
from pygame import *


def motion(mh, command):
    #mh.reset_movement(command)
    print "Command_for_test", command
    mh.move(command)
    if 'new_pos' in command:
        c=command['new_pos']
        screen.move(c[0], c[1], c[2])
    print "moved"

def rotation(spindle, command):
    r=command.pop('M')
    rpm=command.pop('S') if 'S' in command else 2000
    if r==5:
        spindle.stop()
    else:
        spindle.run(rpm)

c_parser=conf_parser()

mh=Steppers_handler(c_parser.get_config('gpio_handler'))

gparser=G_parser.Parser(c_parser.get_config('G_parser'))

spindle=Spindle.Spindle(c_parser.get_config('PWM'))

command_pool=[]

def read_thread():
    while True:
        print "Ready to execute >"
        command = raw_input()
        if command[0:5].upper()=="BREAK":
            command_pool.insert(0,"BREAK")
            mh.break_movement()
            while mh.is_buzy():
                sleep(1)
            print mh.get_move_res()
        elif command[0:8].upper()=="CONTINUE":
            if not mh.is_buzy():
                mh.run()
        elif command[0:4].upper()=="EXIT":
            command_pool.append("EXIT") 
            exit()
        elif command[0:4].upper()=="OPEN":
            gparser.open_file(command[5:])
        elif command[0:3].upper()=="RUN":
            command_pool.append("RUN")
        elif command[0:4].upper()=="STOP":
            command_pool.append("STOP")
        else:
            command_pool.append(command.upper())
        print command_pool

def joystick_handling(c_pool):
    step=0.2
    if not joystick:
        joy=Joy({'keys':['yes','cansel', 'dx+', 'dx-', 'dy+', 'dy-', 'dz+', 'dz-']}, {})
        if not joy.discover():
            return None
    else:
        joy=joystick
    b=joy.get_buttons()
    command = 'G91X'+str((b['dx+']-b['dx-'])*step)+'Y'+str((b['dy+']-b['dy-'])*step)+'Z'+str((b['dz+']-b['dz-'])*step)
    if (b['dx+']-b['dx-']) or (b['dy+']-b['dy-']) or (b['dz+']-b['dz-']):
        c_pool.append(command)
    return joy

screen = cnc_screen({'size':(800, 600)})
screen_active = False
joystick = None
joystick_active = False
p1 = threading.Thread(target=read_thread)
p1.start()

runned=0
joystick=0

while True:
        if joystick_active:
            joystick=joystick_handling(command_pool)
        if runned:
            commands=gparser.get_commands()
            if commands:
                for command in commands:
                    if 'M' in command:
                        rotation(spindle, command)
                    if command:
                        motion(mh, command)
            else:
                print 'EOF'
                runned=0
        elif not joystick_active:
            sleep(1)
        if command_pool:
            command=command_pool.pop(0)
            if command == "EXIT":
                mh.destroy()
                exit(0)
            elif command=="RUN":
                runned=1
            elif command=="RERUN":
                gparser.restart_file()
                runned=1
            elif command=="STOP":
                runned=0
            elif command=="JOY":
                joystick_active=not joystick_active
            elif command=="SCREEN":
                screen.revert_active()
            elif command=='ZOOMIN':
                screen.zoom(1)
            elif command=='ZOOMOUT':
                screen.zoom(-1)
            elif command[0:7]=="REVERSE":
                gparser.reverse(command[8:])
            elif command[0:4].upper()=="TEST":
                gpio_test_params={'dir_y': 0, 'dir_x': 0, 'dir_z': 0, 'interval': 0.01, 'steps_z': 0, 'steps_y': 0, 'steps_x': 0}
                test_command=gparser.convert_line(command[5:])
                for key in test_command.keys():
                    gpio_test_params['steps_'+key.lower()]=test_command[key]
                print command, gpio_test_params
                motion(mh, gpio_test_params)
            elif command[0:5].upper()=="CLEAR":
                screen.clear()
            else:
                if command[0:3]=="G92":
                    screen.g92()
                converted_command=gparser.convert_line(command)
                print command, converted_command
                gparser.process(converted_command)
                if gparser.is_moved() or gparser.spindle['changed']:
                    commands=gparser.get_commands()
                    for command in commands:
                        if 'M' in command:
                            rotation(spindle, command)
                        if command:
                            motion(mh, command)


p1.join()
