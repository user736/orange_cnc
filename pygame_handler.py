#!/usr/bin/env python

import pygame
from pygame import *
import time

class cnc_screen(object):

    def __init__(self, params):
        if 'size' not in params:
            params['size']=(640, 480)
        if 'start_color' not in params:
            params['start_color']='#ff0000'
        if 'md_color' not in params:
            params['md_color']='#00FFFF'
        if 'mapping' not in params:
            params['mapping']={'dx':0, 'dy':0, 'kx':20, 'ky':20, 'min_z':0, 'max_z':1}
        if 'point' not in params:
            params['point']={'x':0, 'y':0, 'z':0}
        if 'mill' not in params:
            params['mill']=0.8
        self.reset_params(params)
        pygame.init()
        self.is_active=True
        self.redraw_display()

    def get_remapped_mill(self):
        res = int(self.mill*self.mapping['kx']/2)
        return res

    def revert_active(self):
        if self.is_active:
            self.quit()
        else:
            self.redraw_display()

    def redraw_display(self):
        self.is_active=True
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Orange CNC "+'X'.join(map(str,self.size)))
        self.screen.fill(Color(self.start_color))
        self.redraw_system()
        self.redraw_figure()
        pygame.display.flip()

    def redraw_system(self):
        mx, my=self.size
        k = self.mapping['kx']
        for x in range(1, mx//k):
            pygame.draw.line(self.screen, Color('#5f5f5f'), [x*k, 0], [x*k,my], 1)
        for y in range(1, my//k):
            pygame.draw.line(self.screen, Color('#5f5f5f'), [0, y*k], [mx, y*k], 1)

    def redraw_figure(self):
        d=self.get_remapped_mill()
        points=self.points
        p_s=self.remap_point(points[0])
        pygame.draw.circle(self.screen, p_s[2], (p_s[0], p_s[1]), d, 0)
        for i in range(1,len(points)):
            self.draw_line(points[i-1], points[i])

    def remap_point(self, point):
        mapping=self.mapping
        disp_x=int(mapping['dx']+mapping['kx']*point['x'])
        disp_y=int(mapping['dy']+mapping['ky']*point['y'])
        color=self.get_color(point['z'])
        return [disp_x, disp_y, color]

    def get_color(self, z):
        min_z=self.mapping['min_z']
        max_z=self.mapping['max_z']
        if z in self.colors:
            return self.colors[z]
        if z<min_z:
            self.mapping['min_z']=z
            self.refill_colors()
            return self.get_color(z)
        if z>max_z:
            self.mapping['max_z']=z
            self.refill_colors()
            return self.get_color(z)
        res=[]
        for i_c in range(3):
            c_min=self.colors[min_z][i_c]
            c_max=self.colors[max_z][i_c]
            c=int(c_min+(c_max-c_min)*(z-min_z)/(max_z-min_z))
            res.append(c)
        self.colors[z]=res
        return res

    def zoom(self, zk):
        k = self.mapping['kx']
        k += zk*10
        if k == 0:
            k = 10
        self.mapping['kx'] = k
        self.mapping['ky'] = k
        if zk:
            self.redraw_display()


    def refill_colors(self):
        min_z=self.mapping['min_z']
        max_z=self.mapping['max_z']
        self.colors={min_z:Color(self.start_color), max_z:Color(self.md_color)}

    def quit(self):
        pygame.display.quit()
        self.is_active=False

    def move(self, x, y, z):
        self.points.append({'x':x, 'y':y, 'z':z})
        self.point={'x':x, 'y':y, 'z':z}
        if self.is_active:
            if len(self.points)>1:
                self.draw_line(self.points[-2], self.points[-1])
                pygame.display.flip()

    def move_90(self, x=0, y=0, z=0):
        x+=self.point['x']
        y+=self.point['y']
        z+=self.point['z']
        self.move(x, y, z)
        
    def draw_line(self, fr, to):
        d=self.get_remapped_mill()
        p_s=self.remap_point(fr)
        p_e=self.remap_point(to)
        pygame.draw.line(self.screen, p_e[2], (p_s[0], p_s[1]), (p_e[0], p_e[1]),2*d)
        pygame.draw.circle(self.screen, p_s[2], (p_s[0], p_s[1]), d, 0)
        pygame.draw.circle(self.screen, p_e[2], (p_e[0], p_e[1]), d, 0)

    def reset_params(self, params):
        if 'size' in params:
            self.size=params['size']
        if 'point' in params:
            self.point=params['point']
        if 'mill' in params:
            self.mill=params['mill']
        colors_changed=False
        if 'mapping' in params:
            self.mapping=params['mapping']
            self.colors_changed=True
        if 'start_color' in params:
            if not (hasattr(self, 'start_color')) or (self.start_color!=params['start_color']):
                self.start_color=params['start_color']
                colors_changed=True
        if 'md_color' in params:
            if not hasattr(self, 'md_color') or self.md_color!=params['md_color']:
                self.md_color=params['md_color']
                colors_changed=True
        if colors_changed:
            self.refill_colors()
        if not hasattr(self, 'points'):
            self.points=[{'x':self.point['x'], 'y':self.point['y'], 'z':self.point['z']}]


def main():
    xd=xu=yd=yu=zd=zu=False
    clock = pygame.time.Clock()
    step=0.2
    screen = cnc_screen({})
    for i in range(7):
        screen.move(i*i, i, 0.1*i)
    while 1:
        for e in pygame.event.get():
            if (e.type == QUIT) or (e.type == KEYDOWN and e.key==27):
                screen.quit()
                time.sleep(3)
                screen.redraw_display()
            #screen.redraw_figure()
            if e.type == KEYDOWN:
                if e.key == K_LEFT:
                    xd=True
                elif e.key == K_RIGHT:
                    xu=True
                elif e.key == K_DOWN:
                    yd=True
                elif e.key == K_UP:
                    yu=True
                elif e.key == 115: #S
                    zd=True
                elif e.key == 119: #W
                    zu=True
                else: print e.key

            if e.type == KEYUP:
                if e.key == K_LEFT:
                    xd=False
                elif e.key == K_RIGHT:
                    xu=False
                elif e.key == K_DOWN:
                    yd=False
                elif e.key == K_UP:
                    yu=False
                elif e.key == 115: #S
                    zd=False
                elif e.key == 119: #W
                    zu=False
                else: print e.key

        screen.move_90((xu-xd)*step, (yu-yd)*step, (zu-zd)*step)
        clock.tick(20)

if __name__ == "__main__":
    main()
