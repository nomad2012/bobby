#!/usr/bin/env python
#
# bobby.py - Bobby the Animated Head
#
import time
import Adafruit_PCA9685
import logging

RCS_MIN_POS = 200
RCS_MAX_POS = 600
RCS_CENTER_POS = (RCS_MIN_POS + RCS_MAX_POS) / 2

SERVO_LEFT_TILT = 0
SERVO_RIGHT_TILT = 1
SERVO_JAW = 2

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

def main():
    global pwm
    #logging.basicConfig(level=logging.DEBUG)
    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(60)
    while True:
        ramp_tilt(TILT_DOWN, TILT_UP)
        ramp_jaw(JAW_CLOSED, JAW_OPEN)
        ramp_tilt(TILT_UP, TILT_DOWN)
        ramp_jaw(JAW_OPEN, JAW_CLOSED)


if __name__ == "__main__":
    main()