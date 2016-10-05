#!/usr/bin/env python
#
# bobby.py - Bobby the Animated Head
#

import curses
import time
import Adafruit_PCA9685
import logging
import math

RCS_MIN_POS = 200
RCS_MAX_POS = 600
RCS_CENTER_POS = (RCS_MIN_POS + RCS_MAX_POS) / 2

SERVO_LEFT_TILT = 0
SERVO_RIGHT_TILT = 1
SERVO_JAW = 2

MOT_1A = 9
MOT_1B = 10
MOT_2A = 11
MOT_2B = 12
MOT_3A = 14
MOT_3B = 13

WHEEL1_ANGLE = math.pi / 2.0
WHEEL2_ANGLE = math.pi + (math.pi / 6.0)
WHEEL3_ANGLE = -math.pi / 6.0

COS_WHEEL1 = math.cos(WHEEL1_ANGLE)
SIN_WHEEL1 = math.sin(WHEEL1_ANGLE)
COS_WHEEL2 = math.cos(WHEEL2_ANGLE)
SIN_WHEEL2 = math.sin(WHEEL2_ANGLE)
COS_WHEEL3 = math.cos(WHEEL3_ANGLE)
SIN_WHEEL3 = math.sin(WHEEL3_ANGLE)


TILT_UP = 320
TILT_CENTER = 380
TILT_DOWN = 470
TILT_LEFT_OFFSET = 400

JAW_CLOSED = 320
JAW_OPEN = 560

servo_pos = [RCS_CENTER_POS, RCS_CENTER_POS, RCS_CENTER_POS]

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
    v1 = v_linear * (COS_WHEEL1 * math.cos(direction) - SIN_WHEEL1 * math.sin(direction)) + v_angular
    v2 = v_linear * (COS_WHEEL2 * math.cos(direction) - SIN_WHEEL2 * math.sin(direction)) + v_angular
    v3 = v_linear * (COS_WHEEL3 * math.cos(direction) - SIN_WHEEL3 * math.sin(direction)) + v_angular

    print "v1={0}, v2={1}, v3={2}\r".format(v1, v2, v3)
    set_motor(MOT_1A, MOT_1B, round(v1))
    set_motor(MOT_2A, MOT_2B, round(v2))
    set_motor(MOT_3A, MOT_3B, round(v3))


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


SPEED = 3000

def main():
    global pwm
    #logging.basicConfig(level=logging.DEBUG)
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(60)

    #init the curses screen
    stdscr = curses.initscr()
    #use cbreak to not require a return key press
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)
    print "\r\npress q to quit\r"
    quit=False
    direction = 0.0
    v_linear = 0.0
    v_angular = 0.0

    tilt_neck(TILT_CENTER)
    # loop
    while quit != True:
        c = stdscr.getch()
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

    move_robot(0.0, 0, 0)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
       
if __name__ == "__main__":
    main()