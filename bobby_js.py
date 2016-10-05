#!/usr/bin/env python
#
# bobby.py - Bobby the Animated Head
#

import curses
import time
import Adafruit_PCA9685
import logging
import math
import select
import struct
import sys

RCS_MIN_POS = 200
RCS_MAX_POS = 600
RCS_CENTER_POS = (RCS_MIN_POS + RCS_MAX_POS) / 2

SERVO_LEFT_TILT = 0
SERVO_RIGHT_TILT = 1
SERVO_JAW = 2

SERVO_RATE = 10

MOT_1A = 9
MOT_1B = 10
MOT_2A = 11
MOT_2B = 12
MOT_3A = 14
MOT_3B = 13

MOT1_SCALE = 1.0
MOT2_SCALE = 0.9
MOT3_SCALE = 0.9

WHEEL1_ANGLE = math.pi / 2.0
WHEEL2_ANGLE = math.pi + (math.pi / 6.0)
WHEEL3_ANGLE = -math.pi / 6.0

COS_WHEEL1 = math.cos(WHEEL1_ANGLE)
SIN_WHEEL1 = math.sin(WHEEL1_ANGLE)
COS_WHEEL2 = math.cos(WHEEL2_ANGLE)
SIN_WHEEL2 = math.sin(WHEEL2_ANGLE)
COS_WHEEL3 = math.cos(WHEEL3_ANGLE)
SIN_WHEEL3 = math.sin(WHEEL3_ANGLE)

WHEEL_SPEED_MAX = 4095

TILT_UP = 320
TILT_CENTER = 380
TILT_DOWN = 470
TILT_LEFT_OFFSET = 400

JAW_CLOSED = 320
JAW_OPEN = 560


# joystick event types
JS_EVENT_SIZE = struct.calcsize("lhBB")

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

# joystick axis numbers
JS_LX_AXIS = 0
JS_LY_AXIS = 1
JS_RX_AXIS = 2
JS_RY_AXIS = 3
JS_HX_AXIS = 4
JS_HY_AXIS = 5

JS_AXIS_MIN = -32767
JS_AXIS_MAX = 32767

# joystick button numbers
JS_SQUARE_BUTTON = 0
JS_X_BUTTON = 1
JS_O_BUTTON = 2
JS_TRIANGLE_BUTTON = 3
JS_L_TRIGGER2_BUTTON = 4
JS_R_TRIGGER2_BUTTON = 5
JS_L_TRIGGER_BUTTON = 6
JS_R_TRIGGER_BUTTON = 7
JS_STOP_BUTTON = 8
JS_PLAY_BUTTON = 9
JS_HOME_BUTTON = 12

# joystick button event values
JS_BUTTON_PRESSED = 1
JS_BUTTON_RELEASED = 0

JS_EVENT_TYPES = { JS_EVENT_BUTTON : 'BUTTON', JS_EVENT_AXIS : 'AXIS', JS_EVENT_INIT : 'INIT' }

JS_AXIS_NUMBERS = { JS_LX_AXIS : 'LEFT_X', 
                    JS_LY_AXIS : 'LEFT_Y',
                    JS_RX_AXIS : 'RIGHT_X',
                    JS_RY_AXIS : 'RIGHT_Y',
                    JS_HX_AXIS : 'HAT_X',
                    JS_HY_AXIS : 'HAT_Y' }

JS_BUTTON_NUMBERS = { JS_SQUARE_BUTTON : 'SQUARE',
                      JS_X_BUTTON : 'X',
                      JS_O_BUTTON : 'O',
                      JS_TRIANGLE_BUTTON : 'TRIANGLE',
                      JS_L_TRIGGER2_BUTTON : 'L_TRIGGER2',
                      JS_R_TRIGGER2_BUTTON : 'R_TRIGGER2',
                      JS_L_TRIGGER_BUTTON : 'L_TRIGGER',
                      JS_R_TRIGGER_BUTTON : 'R_TRIGGER',
                      JS_STOP_BUTTON : 'STOP',
                      JS_PLAY_BUTTON : 'PLAY',
                      JS_HOME_BUTTON : 'HOME' }
                      
JS_BUTTON_VALUES = { JS_BUTTON_RELEASED : 'RELEASED', JS_BUTTON_PRESSED : 'PRESSED' }


servo_min = [TILT_UP, TILT_UP, JAW_CLOSED]
servo_max = [TILT_DOWN, TILT_DOWN, JAW_OPEN]

servo_pos = [RCS_CENTER_POS, RCS_CENTER_POS, RCS_CENTER_POS]
servo_targets = [TILT_CENTER, TILT_CENTER, JAW_CLOSED]


def tilt_neck(angle):
    a = min(max(angle, TILT_UP), TILT_DOWN)
    pwm.set_pwm(SERVO_LEFT_TILT, 0, TILT_LEFT_OFFSET - (a - TILT_LEFT_OFFSET))
    servo_pos[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (a - TILT_LEFT_OFFSET)
    pwm.set_pwm(SERVO_RIGHT_TILT, 0, a)
    servo_pos[SERVO_RIGHT_TILT] = a

def ramp_tilt(start, end):
    a = start
    while a != end:
        tilt_neck(a)
        time.sleep(0.02)
        if start > end:
            a -= 3
        else:
            a += 3
    tilt_neck(end)
            
def ramp_jaw(start, end):
    a = start
    while a != end:
        pwm.set_pwm(SERVO_JAW, 0, a)
        servo_pos[SERVO_JAW] = a
        time.sleep(0.02)
        if start > end:
            a -= 40
        else:
            a += 40
    pwm.set_pwm(SERVO_JAW, 0, end)


def ramp_pin(pin, start, end, step=1):
    a = start
    while a != end:
        print "set pin {0} to {1}".format(pin, a)
        pwm.set_pwm(pin, 0, a)
        time.sleep(0.02)
        if start > end:
            a -= step
            if a < end:
                a = end
        else:
            a += step
            if a > end:
                a = end

def set_motor(pinA, pinB, speed):
    s = int(speed)
    if s > 0:
        pwm.set_pwm(pinA, 0, 0)
        pwm.set_pwm(pinB, 0, s)
    else:
        pwm.set_pwm(pinA, 0, abs(s))
        pwm.set_pwm(pinB, 0, 0)

def move_robot(direction, v_linear, v_angular):
    print "dir={0}, v_linear={1}, v_angular={2}".format(direction, v_linear, v_angular)
    
    v1 = v_linear * (COS_WHEEL1 * math.cos(direction) - SIN_WHEEL1 * math.sin(direction)) + v_angular
    v2 = v_linear * (COS_WHEEL2 * math.cos(direction) - SIN_WHEEL2 * math.sin(direction)) + v_angular
    v3 = v_linear * (COS_WHEEL3 * math.cos(direction) - SIN_WHEEL3 * math.sin(direction)) + v_angular

    print "v1={0}, v2={1}, v3={2}\r".format(v1, v2, v3)
    set_motor(MOT_1A, MOT_1B, max(min(round(v1) * MOT1_SCALE, WHEEL_SPEED_MAX), -WHEEL_SPEED_MAX))
    set_motor(MOT_2A, MOT_2B, max(min(round(v2) * MOT2_SCALE, WHEEL_SPEED_MAX), -WHEEL_SPEED_MAX))
    set_motor(MOT_3A, MOT_3B, max(min(round(v3) * MOT3_SCALE, WHEEL_SPEED_MAX), -WHEEL_SPEED_MAX))

    
def calc_servo_positions(positions, targets, rate):

    new_positions = []
    for pos, targ in zip(positions, targets):
        if pos < targ:
            new_positions.append(min(pos + rate, targ))
        elif pos > targ:
            new_positions.append(max(pos - rate, targ))
        else:
            new_positions.append(pos)
    return new_positions

def position_servos(positions):
    for i in range(len(positions)):
        pwm.set_pwm(i, 0, positions[i])
    
def test_motors():
    ramp_tilt(TILT_DOWN, TILT_UP)
    ramp_jaw(JAW_CLOSED, JAW_OPEN)
    ramp_tilt(TILT_UP, TILT_DOWN)
    ramp_jaw(JAW_OPEN, JAW_CLOSED)
    
    pwm.set_pwm(MOT_1B, 0, 0)
    ramp_pin(MOT_1A, 0, 4095, 10)
    ramp_pin(MOT_1B, 0, 4095, 10)
    ramp_pin(MOT_1A, 4095, 0, 10)
    ramp_pin(MOT_1B, 4095, 0, 10)

    pwm.set_pwm(MOT_2B, 0, 0)
    ramp_pin(MOT_2A, 0, 4095, 10)
    ramp_pin(MOT_2B, 0, 4095, 10)
    ramp_pin(MOT_2A, 4095, 0, 10)
    ramp_pin(MOT_2B, 4095, 0, 10)

    pwm.set_pwm(MOT_3B, 0, 0)
    ramp_pin(MOT_3A, 0, 4095, 10)
    ramp_pin(MOT_3B, 0, 4095, 10)
    ramp_pin(MOT_3A, 4095, 0, 10)
    ramp_pin(MOT_3B, 4095, 0, 10)



def read_js_event(js_states):
    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        event = sys.stdin.read(JS_EVENT_SIZE)
        e_time, e_value, e_type, e_num = struct.unpack("lhBB", event)
        print e_type, e_num, e_value
        e_list = []
        if e_type & JS_EVENT_INIT:
            e_list.append(JS_EVENT_TYPES[JS_EVENT_INIT])
        if e_type & JS_EVENT_BUTTON:
            e_list.append(JS_EVENT_TYPES[JS_EVENT_BUTTON])
            e_list.append(JS_BUTTON_NUMBERS.get(e_num, e_num))
            e_list.append(JS_BUTTON_VALUES[e_value])
            js_states[JS_BUTTON_NUMBERS.get(e_num, e_num)] = e_value
        if e_type & JS_EVENT_AXIS:
            e_list.append(JS_EVENT_TYPES[JS_EVENT_AXIS])
            e_list.append(JS_AXIS_NUMBERS.get(e_num, e_num))
            e_list.append(e_value)
            js_states[JS_AXIS_NUMBERS.get(e_num, e_num)] = e_value          
        print e_list
        
    return js_states

    
SPEED = 3000

def interpret_key(c):

    print curses.keyname(c)
    if curses.keyname(c) == "q":
        quit = True
    elif curses.keyname(c) == "a":
        v_angular = SPEED
    elif curses.keyname(c) == "s":
        v_angular = 0
    elif curses.keyname(c) == "d":
        v_angular = -SPEED
    elif curses.keyname(c) == "1":
        direction = -math.pi * 3.0 / 2.0
        v_linear = SPEED
    elif curses.keyname(c) == "2":
        direction = math.pi
        v_linear = SPEED
    elif curses.keyname(c) == "3":
        direction = math.pi * 3.0 / 2.0
        v_linear = SPEED
    elif curses.keyname(c) == "4":
        direction = math.pi / 2.0
        v_linear = SPEED
    elif curses.keyname(c) == "5":
        direction = 0.0
        v_linear = 0.0
    elif curses.keyname(c) == "6":
        direction = -math.pi / 2.0
        v_linear = SPEED
    elif curses.keyname(c) == "7":
        direction = math.pi / 4.0
        v_linear = SPEED
    elif curses.keyname(c) == "8":
        direction = 0.0
        v_linear = SPEED
    elif curses.keyname(c) == "9":
        direction = -math.pi / 4.0
        v_linear = SPEED
        
    move_robot(direction, v_linear, v_angular)


def main():
    global pwm
    global js_state
    global servo_pos
    global servo_targets
    #logging.basicConfig(level=logging.DEBUG)
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(60)
    js_state = {}
    quit=False
    direction = 0.0
    v_linear = 0.0
    v_angular = 0.0
    neck_left_tilt = TILT_CENTER

    tilt_neck(TILT_CENTER)
    # loop
    
    while quit != True:
        js_state = read_js_event(js_state)

        if js_state.get(JS_BUTTON_NUMBERS[JS_HOME_BUTTON]):
            quit = True
            
        rotate = js_state.get(JS_AXIS_NUMBERS[JS_RX_AXIS])
        if rotate is not None:
            v_angular = -rotate * WHEEL_SPEED_MAX / JS_AXIS_MAX

        x_value = js_state.get(JS_AXIS_NUMBERS[JS_LX_AXIS])
        y_value = js_state.get(JS_AXIS_NUMBERS[JS_LY_AXIS])
        if x_value is not None and y_value is not None:
            x_value = -x_value
            y_value = -y_value
            direction = math.atan2(x_value, y_value)
            v_linear = math.sqrt(x_value * x_value + y_value * y_value) * WHEEL_SPEED_MAX / JS_AXIS_MAX

        r_trigger = js_state.get(JS_BUTTON_NUMBERS[JS_R_TRIGGER_BUTTON])
        if r_trigger:
            servo_targets[SERVO_JAW] = JAW_OPEN
        else:
            servo_targets[SERVO_JAW] = JAW_CLOSED

        hat_x = js_state.get(JS_AXIS_NUMBERS[JS_HX_AXIS])
        if hat_x:
            if hat_x < 0:
                servo_targets[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (TILT_UP - TILT_LEFT_OFFSET)
                servo_targets[SERVO_RIGHT_TILT] = TILT_DOWN
            else:
                servo_targets[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (TILT_DOWN - TILT_LEFT_OFFSET)
                servo_targets[SERVO_RIGHT_TILT] = TILT_UP

        hat_y = js_state.get(JS_AXIS_NUMBERS[JS_HY_AXIS])
        if hat_y:
            if hat_y < 0:
                servo_targets[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (TILT_DOWN - TILT_LEFT_OFFSET)
                servo_targets[SERVO_RIGHT_TILT] = TILT_DOWN
            else:
                servo_targets[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (TILT_UP - TILT_LEFT_OFFSET)
                servo_targets[SERVO_RIGHT_TILT] = TILT_UP
        elif not hat_x:
            servo_targets[SERVO_LEFT_TILT] = TILT_LEFT_OFFSET - (TILT_CENTER - TILT_LEFT_OFFSET)
            servo_targets[SERVO_RIGHT_TILT] = TILT_CENTER
               
                          
            
        move_robot(direction, v_linear, v_angular)
        servo_pos = calc_servo_positions(servo_pos, servo_targets, SERVO_RATE)
        position_servos(servo_pos)
        
    move_robot(0.0, 0, 0)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
       
if __name__ == "__main__":
    main()
