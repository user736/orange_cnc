#!/usr/bin/env python

import signal, sys, time
from Conf import conf_parser
from  gpio_handler import Movement_handler
import G_parser
import threading

c_parser=conf_parser()

mh=Movement_handler(c_parser.get_config('gpio_handler'))

gparser=G_parser.Parser(c_parser.get_config('G_parser'))

command_pool=[]

def read_thread():
    while True:
        print "Ready to execute >"
        command = raw_input()
        if command[0:5].upper()=="BREAK":
            command_pool.insert(0,"BREAK")
            mh.break_movement()
            while mh.is_buzy():
                time.sleep(1)
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


p1 = threading.Thread(target=read_thread)
p1.start()

runned=0

while True:
        if runned:
            p=gparser.get_commands()
            if p:
                mh.reset_movement(p)
                mh.run()
                while mh.is_buzy():
                    signal.pause()
            else:
                print 'EOF'
                runned=0
        else:
            time.sleep(1)
        if command_pool:
            command=command_pool.pop(0)
            if command == "EXIT":
                exit(0)
            elif command=="RUN":
                runned=1
            elif command=="STOP":
                runned=0
            elif command[0:4].upper()=="TEST":
                gpio_test_params={'dir_y': 0, 'dir_x': 0, 'dir_z': 0, 'interval': 0.01, 'steps_z': 0, 'steps_y': 0, 'steps_x': 0}
                test_command=gparser.convert_line(command[5:])
                for key in test_command.keys():
                    gpio_test_params['steps_'+key.lower()]=test_command[key]
                print command, gpio_test_params
                mh.reset_movement(gpio_test_params)
                mh.run()
            else:
                converted_command=gparser.convert_line(command)
                print command, converted_command
                gparser.process(converted_command)
                if gparser.is_moved():
                    p=gparser.get_commands()
                    mh.reset_movement(p)
                    mh.run()
                    while mh.is_buzy():
                        signal.pause()


p1.join()
