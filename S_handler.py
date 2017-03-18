#!/usr/bin/env python

from multiprocessing import Process, Pipe
from Stepper import Stepper

def new_child(conn, params):
    stepper = Stepper(params)
    while 1:
        s = conn.recv()
        if s=='RUN':
            runres=stepper.run()
            conn.send(runres)
        elif s=='RESET':
            stepper.reset_params(params)
        elif s=="DESTROY":
            return 0
        else:
            param, val = s.split()
            if param in ('steps_pin', 'dir_pin', 'steps2sync', 'steps', 'dir'):
                val = int(val)
            elif param in ('interval'):
                val = float(val)
            params[param]=val


class Steppers_handler(object):

    def __init__(self, params):
        Axes={}
        for axis in params["axes"]:
            proc={}
            parent_conn, child_conn = Pipe()
            proc["process"] = Process(target=new_child, args=(child_conn, params["axes"][axis]))
            proc["child_conn"] = child_conn
            proc["parent_conn"] = parent_conn
            Axes[axis]=proc
            proc["process"].start()
            #proc["process"].join()
        self.Axes=Axes

    def send_params(self, pipe, params):
        for p in params:
            pipe.send(p+' '+str(params[p]))
        pipe.send('RESET')

    def destroy(self):
        for axis in self.Axes:
            self.Axes[axis]["parent_conn"].send("DESTROY")

    def move(self, params):
        conn_ids=[]
        self.add_steps2sync(params, self.calc_divider(params))
        Axes=self.Axes
        for axis in Axes:
            if axis in params:
                conn_ids.append(axis)
                pipe = Axes[axis]["parent_conn"]
                self.send_params(pipe, params[axis])
                pipe.send('RUN')
        self.wait(conn_ids)

    def add_steps2sync(self, params, divider):
        for axis in params:
            if axis in self.Axes:
                params[axis]["steps2sync"]=params[axis]["steps"]//divider+(params[axis]["steps"]%divider > 0)

    def calc_divider(self, params):
        return 3

    def wait(self, conn_ids):
        Conns={}
        for id in conn_ids:
            Conns[id]=self.Axes[id]["parent_conn"]
        while Conns:
            t_conns={}
            for id in Conns:
                res=Conns[id].recv()
                if res:
                    t_conns[id]=Conns[id]
            Conns = t_conns
            print 2, Conns    
            for id in Conns:
                Conns[id].send("RUN")

if __name__=='__main__':

    params =  {"axes":{
            "x":{ "steps_pin":20, "dir_pin":8 },
            "y":{ "steps_pin":10, "dir_pin":7 },
            "z":{ "steps_pin":9, "dir_pin":19 }
        }}

    SH = Steppers_handler(params)
    SH.move({'x':{"steps":20}, 'y':{"steps":120}, "z":{"steps":270,"interval":0.03}})


    while True:
        print raw_input()
