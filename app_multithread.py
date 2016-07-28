#!/usr/bin/env python

import signal, sys, time
#from pyA20.gpio import gpio
#from pyA20.gpio import port
#from pyA20.gpio import connector
from  gpio_handler import Movement_handler
import G_parser
import threading

params={}
mh=Movement_handler(params)
mh.run()

gparser=G_parser.Parser("cnc.cfg")
print gparser.params

command_pool=[]

def read_thread():
    while True:
        print "Ready to execute"
        command = raw_input()
        if command[0:4].upper()=="OPEN":
            gparser.open_file(command[5:])
        elif command[0:3].upper()=="RUN":
            command_pool.append("RUN")
        elif command[0:4].upper()=="STOP":
            command_pool.append("STOP")
        else:
            command_pool.append(command.apper())
        print command_pool

def execute_thread():
    runned=0
        
        

p1 = threading.Thread(target=read_thread)
p2 = threading.Thread(target=execute_thread)
p1.start()
p2.start()
runned=0
while True:
        if runned:
            p=gparser.get_commands()
            if p:
                print p
                mh.reset_params(p)
                mh.run()
                while mh.is_buzy():
                    signal.pause()
                    #time.sleep(0.01)
            else:
                print 'EOF'
                runned=0
        else:
            time.sleep(1)
            #print "wait",  command_pool
        if command_pool:
            command=command_pool.pop(0)
            if command=="RUN":
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
                    mh.reset_params(p)
                    mh.run()
                    while mh.is_buzy():
                        signal.pause()


p1.join()
p2.join()
