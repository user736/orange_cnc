#!/usr/bin/env python

import signal, sys, time
from Conf import conf_parser
from  gpio_handler import Movement_handler
import G_parser
import threading

c_parser=conf_parser()

mh=Movement_handler(c_parser.get_config('gpio_handler'))
print mh.params
mh.run()

gparser=G_parser.Parser(c_parser.get_config('G_parser'))
print gparser.params

command_pool=[]

def read_thread():
    while True:
        print "Ready to execute >"
        command = raw_input()
        if command[0:4].upper()=="EXIT":
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
                print p
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
            else:
                converted_command=gparser.convert_line(command)
                print command, converted_command
                gparser.process(converted_command)
                if gparser.is_moved():
                    p=gparser.get_commands()
                    print p
                    mh.reset_movement(p)
                    mh.run()
                    while mh.is_buzy():
                        signal.pause()


p1.join()
