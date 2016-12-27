from pygame_handler import *
from joystick import *
from pygame import *
import time

j=joy({'keys':['yes','cansel', 'dx+', 'dx-', 'dy+', 'dy-', 'dz+', 'dz-']}, {})
j.discover()

clock = pygame.time.Clock()
step=0.2
screen = cnc_screen({})
#for i in range(7):
#        screen.move(i*i, i, 0.1*i)
while 1:
    for e in pygame.event.get():
        if (e.type == QUIT) or (e.type == KEYDOWN and e.key==27):
            screen.quit()
            time.sleep(3)
            screen.redraw_display()
    b=j.get_buttons()
    screen.move_91((b['dx+']-b['dx-'])*step, (b['dy+']-b['dy-'])*step, (b['dz+']-b['dz-'])*step)
    clock.tick(20)
