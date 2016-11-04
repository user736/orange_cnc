#!/usr/bin/env python

import signal, sys, time 
import ConfigParser
import re, math

class Parser(object):
    def __init__(self, params):
        self.params=params
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
        self.d_alpha=math.pi/360
        self.spindle={'changed':0}
############---Setters---############

    def set_mode(self, value):
        self.mode=value

    def set_feed_mode(self, value):
        self.feed_mode=value

    def set_shape(self, value):
        self.shape=value

    def get_shape(self):
        if hasattr(self, 'shape'):
            return self.shape
        else:
            return 1

    def set_polar_plane(self, value):
        polar_plane_map={17:'XY', 18:'XZ', 19:'YZ'}
        self.polar_plane=polar_plane_map[value]

    def get_polar_plane(self):
        if hasattr(self, 'polar_plane'):
            return self.polar_plane
        else:
            return 'XY'

    def set_clockwise(self, value):
        self.clockwise=value

    def get_clockwise(self):
        if hasattr(self, 'clockwise'):
            return self.clockwise
        else:
            return 0

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

    def get_coordinates(self):
        return {'X':self.curr_x, 'Y':self.curr_y, 'Z':self.curr_z}

###########---Getters---##########

    def open_file(self, fname):
        self.f_handler=open(fname, 'r')

    def read_line(self):
        line = self.f_handler.readline()
        return line

    def convert_line(self, line):
        expr=re.compile(r'([GXYZMSFRIJK]-*\d+\.*\d*)')
        instructions={}
        for instr in expr.findall(line.upper()):
            instructions[instr[0]]=float(instr[1:])
        self.command=instructions
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
            if instructions['G'] in (17,18,19):
                self.set_polar_plane(instructions['G'])
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
        if 'M' in instructions:
            self.spindle['changed']=1
            self.spindle['M']=instructions['M']
            if 'S' in instructions:
                self.spindle['S']=instructions['S']

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
        if not steps_s:
            return None
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

    def calc_circle_center(self, x1, y1, x2, y2, r):
        l=((x1-x2)**2+(y1-y2)**2)**0.5
        h=(r**2-(l/2)**2)**0.5
        xc=(x1+x2)/2
        yc=(y1+y2)/2
        if y1==y2:
            dx=0
            dy=(r**2-((x1-x2)/2)**2)**0.5
        else:
            k=-(x2-x1)/(y2-y1)
        #    b=yc-k*xc
            dx=h*math.cos(math.atan(k))
            dy=k*dx
#       v1=(x1-(xc+dx),y1-(yc+dy))
#       v2=(x2-(xc+dx),y2-(yc+dy))
        v_multi=(y1-(yc+dy))*(x2-(xc+dx))-(x1-(xc+dx))*(y2-(yc+dy))
        if v_multi<0 and not self.get_clockwise() or v_multi>0 and self.get_clockwise():
            return ((xc+dx),(yc+dy))
        else:
            return ((xc-dx),(yc-dy))

    def calc_bow_points(self, c1, c2, b1, b2, e1, e2):
        points=[{'p1':b1,'p2':b2}]
        b_1=b1-c1
        b_2=b2-c2
        r_b=((b1-c1)**2+(b2-c2)**2)**0.5
        alpha_b=math.acos(b_1/r_b)
        if b_2<0:
            alpha_b=-alpha_b
        e_1=e1-c1
        e_2=e2-c2
        r_e=((e1-c1)**2+(e2-c2)**2)**0.5
        alpha_e=math.acos(e_1/r_e)
        if e_2<0:
            alpha_e=-alpha_e
        if not self.get_clockwise():
            d_alpha=self.d_alpha
            if alpha_e<alpha_b:
                alpha_e+=math.pi*2
        else:
            d_alpha=-self.d_alpha
            if alpha_e>alpha_b:
                alpha_e-=math.pi*2
        for i in range( int((alpha_e-alpha_b)/d_alpha)):
            alpha_b+=d_alpha
            b_1=r_b*math.cos(alpha_b)
            b_2=r_b*math.sin(alpha_b)
            points.append({'p1':b_1+c1,'p2':b_2+c2})
        points.append({'p1':e1,'p2':e2})
        return points

    def remap_bow_poins(self,points):
        res=[]
        p_p=self.get_polar_plane()
        for point in points:
            res_point={'X':self.exp_x, 'Y':self.exp_y, 'Z':self.exp_z}
            res_point[p_p[0]]=point['p1']
            res_point[p_p[1]]=point['p2']
            res.append(res_point)
        return res

    def calc_g2_3_points(self,center):
        p_p=self.get_polar_plane()
        g2_3_map={'X':'I','Y':'J','Z':'K'}
        if 'C1' in center:
            c1=center['C1']
        else:
            c1=center[g2_3_map[p_p[0]]]
        if 'C2' in center:
            c2=center['C2']
        else:
            c2=center[g2_3_map[p_p[1]]]
        b1=self.__getattribute__('exp_'+p_p[0].lower())
        b2=self.__getattribute__('exp_'+p_p[1].lower())
        e1=self.__getattribute__('next_'+p_p[0].lower())
        e2=self.__getattribute__('next_'+p_p[1].lower())
        points=self.calc_bow_points(c1,c2,b1,b2,e1,e2)
        res=self.remap_bow_poins(points)
        return res

    def is_moved(self):
        return self.next_x-self.exp_x or self.next_y-self.exp_y or self.next_z-self.exp_z

    def get_commands(self):
        while not (self.is_moved() or self.spindle['changed']):
            s=self.read_line()
            if not(s):
                return None
            print self, s
            self.process(self.convert_line(s))
        res=[]
        if self.spindle['changed']:
            self.spindle['changed']=0
            comm={'M':self.spindle['M']}
            if 'S' in self.spindle:
                comm['S']=self.spindle['S']
            res.append(comm)
        if not self.is_moved():
            return res
        if self.get_shape()==1:
            res.append(self.generate_line_comand(self.next_x-self.exp_x, self.next_y-self.exp_y, self.next_z-self.exp_z))
        else:
            if 'R' in self.command:
                c1,c2= self.calc_circle_center(self.exp_x, self.exp_y, self.next_x, self.next_y, self.command['R'])
                center={'C1':c1,'C2':c2}
            else:
                center={}
                for c in 'IJK':
                    if c in self.command:
                        center[c]=self.command[c]
            points=self.calc_g2_3_points(center)
            sx, sy, sz=points[0]['X'], points[0]['Y'], points[0]['Z']
            for i in range(1,len(points)):
                l_com=self.generate_line_comand(points[i]['X']-sx, points[i]['Y']-sy, points[i]['Z']-sz)
                if l_com:
                    res.append(l_com)
                    sx, sy, sz=points[i]['X'], points[i]['Y'], points[i]['Z']
        return res
