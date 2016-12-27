#!/usr/bin/python


import pygame
import time
import sys
from pygame.locals import *

class Joy(object):

    def __init__(self, params, joy_configs, screen = 0):
        self.params=params
        self.config = {}
        self.joy_configs=joy_configs
        pygame.init()
        pygame.joystick.init()
        pygame.display.init()
        if not screen:
            screen = pygame.display.set_mode((800, 600))
        screen.fill((255,0,0))
        self.screen=screen
        #screen.blit()

    def discover(self):
        j_count = pygame.joystick.get_count()
        if not j_count:
            print "Joystick is not found"
            return False
        else:
            self.joy=pygame.joystick.Joystick(0)
            if j_count > 1:
                print 'Found joysticks'
                for i in range(j_count):
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    print i, '-', joystick.get_name()
                print 'Press any key on selected joystick'
                i_joy = self.select_joy_by_key()
                print pygame.joystick.Joystick(i_joy).get_name, 'selected'
                self.joy=pygame.joystick.Joystick(i_joy)
                selected = True
                for i in range(j_count):
                    if i != i_joy:
                        pygame.joystick.Joystick(i).quit()
            else:
                self.joy=pygame.joystick.Joystick(0)
                self.joy.init()
            print self.joy.get_name()
            self.configure()
        return True

    def configure(self):
        reconf=False
        keys=self.params['keys']
        joy_configs=self.joy_configs
        joy=self.joy
        name = joy.get_name()
        #joy_configs[name]='test'
        print name, joy_configs
        if name in joy_configs.keys():
            joy_conf=joy_configs[name]
            for key in joy_conf:
                keys.remove(key)
            if not keys:
                print "Gonfig for", name, "exists", "\nShould joystick be reconfigured?"
                k=self.get_key_from_list(['yes', 'cansel'])
                if k == 'cansel':
                    return False
                elif k == 'yes':
                    reconf=True
        for key in keys:
            success=False
            self.screen.fill((255,0,0))
            write_text(self.screen, "Press the " + key + " button", 100, 100)
            pygame.display.flip()
            while not success:
                success=self.configure_button(key)
                time.sleep(0.02)
            print >> sys.stderr, 'key', key, self.config[key] 
        print >> sys.stderr, self.config   

    def configure_button(self, button):
        pygame.event.get()
        js = self.joy
        print 'num_buttons', js.get_numbuttons()
        # check buttons for activity...
        for button_index in range(js.get_numbuttons()):
            button_pushed = js.get_button(button_index)
            print button_pushed
            if button_pushed and not self.is_button_used(button_index):
                self.config[button] = ('is_button', button_index)
                return True

        # check hats for activity...
        for hat_index in range(js.get_numhats()):
            hat_status = js.get_hat(hat_index)
            if hat_status[0] < -.5 and not self.is_hat_used(hat_index, 'x', -1):
                self.config[button] = ('is_hat', hat_index, 'x', -1)
                return True
            elif hat_status[0] > .5 and not self.is_hat_used(hat_index, 'x', 1):
                self.config[button] = ('is_hat', hat_index, 'x', 1)
                return True
            if hat_status[1] < -.5 and not self.is_hat_used(hat_index, 'y', -1):
                self.config[button] = ('is_hat', hat_index, 'y', -1)
                return True
            elif hat_status[1] > .5 and not self.is_hat_used(hat_index, 'y', 1):
                self.config[button] = ('is_hat', hat_index, 'y', 1)
                return True

        # check trackballs for activity...
        for ball_index in range(js.get_numballs()):
            ball_status = js.get_ball(ball_index)
            if ball_status[0] < -.5 and not self.is_ball_used(ball_index, 'x', -1):
                self.config[button] = ('is_ball', ball_index, 'x', -1)
                return True
            elif ball_status[0] > .5 and not self.is_ball_used(ball_index, 'x', 1):
                self.config[button] = ('is_ball', ball_index, 'x', 1)
                return True
            if ball_status[1] < -.5 and not self.is_ball_used(ball_index, 'y', -1):
                self.config[button] = ('is_ball', ball_index, 'y', -1)
                return True
            elif ball_status[1] > .5 and not self.is_ball_used(ball_index, 'y', 1):
                self.config[button] = ('is_ball', ball_index, 'y', 1)
                return True

        # check axes for activity...
        for axis_index in range(js.get_numaxes()):
            axis_status = js.get_axis(axis_index)
            if axis_status < -0.5 and not self.is_axis_used(axis_index, -1):
                self.config[button] = ('is_axis', axis_index, -1)
                return True
            elif axis_status > 0.5 and not self.is_axis_used(axis_index, 1):
                self.config[button] = ('is_axis', axis_index, 1)
                return True

        return False

    def get_buttons(self):
        pygame.event.get()
        js = self.joy
        res={}
        for button in self.config:

            # determine what something like "Y" actually means in terms of the joystick
            config = self.config.get(button)
            if config != None:

                # if the button is configured to an actual button...
                if config[0] == 'is_button':
                    res[button] = js.get_button(config[1])

                # if the button is configured to a hat direction...
                elif config[0] == 'is_hat':
                    status = js.get_hat(config[1])
                    if config[2] == 'x':
                        amount = status[0]
                    else:
                        amount = status[1]
                    res[button] = amount == config[3]

                # if the button is configured to a trackball direction...
                elif config[0] == 'is_ball':
                    status = js.get_ball(config[1])
                    if config[2] == 'x':
                        amount = status[0]
                    else:
                        amount = status[1]
                    if config[3] == 1:
                        pushed = amount > 0.5
                    else:
                        pushed = amount < -0.5
                    res[button] = pushed

                # if the button is configured to an axis direction...
                elif config[0] == 'is_axis':
                    status = js.get_axis(config[1])
                    if config[2] == 1:
                        pushed = status if status > 0 else 0
                    else:
                        pushed = abs(status) if status < 0 else 0
                    res[button] = pushed
        return res

    def select_joy_by_key(self):
        key = 0
        while not key:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    i_joy = event.joy
                    key = 1
                    return i_joy

    def is_button_used(self, button_index):
        for button in self.params['keys']:
            config = self.config.get(button)
            if config != None and config[0] == 'is_button' and config[1] == button_index:
                return True
        return False

    def is_hat_used(self, hat_index, axis, direction):
        for button in self.params['keys']:
            config = self.config.get(button)
            if config != None and config[0] == 'is_hat':
                if config[1] == hat_index and config[2] == axis and config[3] == direction:
                    return True
        return False

    def is_ball_used(self, ball_index, axis, direction):
        for button in self.params['keys']:
            config = self.config.get(button)
            if config != None and config[0] == 'is_ball':
                if config[1] == ball_index and config[2] == axis and config[3] == direction:
                    return True
        return False

    def is_axis_used(self, axis_index, direction):
        for button in self.params['keys']:
            config = self.config.get(button)
            if config != None and config[0] == 'is_axis':
                if config[1] == axis_index and config[2] == direction:
                    return True
        return False



pygame.init()
cached_text = {}
cached_font = None
def write_text(screen, text, x, y):
    global cached_text, cached_font
    image = cached_text.get(text)
    if image == None:
        if cached_font == None:
            cached_font = pygame.font.Font(pygame.font.get_default_font(), 12)
        image = cached_font.render(text, True, (255, 255, 255))
        cached_text[text] = image
    screen.blit(image, (x, y - image.get_height()))

def main():
    screen = pygame.display.set_mode((640, 480)) 
    write_text(screen, 'text', 50, 50)
    j=Joy({'keys':['yes','cansel', 'dx+', 'dx-', 'dy+', 'dy-', 'dz+', 'dz-']}, {}, screen)
    j.discover()
    for i in range(5):
        print j.get_buttons()
        time.sleep(1)

if __name__ == "__main__":
    main()

