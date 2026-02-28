#pin/pwm library esp32
from machine import Pin, PWM
#system library for serial
import sys
#struct for unpacking
import struct


#pwm object on pin 5 and 18
#backleft wheel
#5 is forward
#18 is backward
wheel1_f = PWM(Pin(5), freq=2000, duty=0)
wheel1_b = PWM(Pin(18), freq=2000, duty=0)

#pwm object on pin 19 and 21
#frontleft wheel
#19 is forward
#21 is backward
wheel2_f = PWM(Pin(19), freq=2000, duty=0)
wheel2_b = PWM(Pin(21), freq=2000, duty=0)

#pwm object on pin 26 and 25
wheel3_f = PWM(Pin(26), freq=2000, duty=0)
wheel3_b = PWM(Pin(25), freq=2000, duty=0)

#pwm objet on pin 33 and 32
wheel4_f = PWM(Pin(33), freq=2000, duty=0)
wheel4_b = PWM(Pin(32), freq=2000, duty=0)




#message packet (wheel id [int], wheel duty [int])
#main function
if (__name__ == "__main__"):
    
    #loop for reading messages
    while(True):
        pass
        #num
        msg = sys.stdin.readline().strip()
        #duty
        dmsg = sys.stdin.readline().strip()
        
        id_ = int(msg)
        duty=int(dmsg)
       
        #wheel1 output
        if(id_ == 1):
            wheel1_f.duty(duty)
            wheel1_b.duty(0)
        if(id_ == -1):
            wheel1_b.duty(duty)
            wheel1_f.duty(0)
            
        #wheel2 output
        if(id_ == 2):
            wheel2_f.duty(duty)
            wheel2_b.duty(0)
        if(id_ == -2):
            wheel2_b.duty(duty)
            wheel2_f.duty(0)
            
        #wheel3 output
        if(id_ == 3):
            wheel3_f.duty(duty)
            wheel3_b.duty(0)
        if(id_ == -3):
            wheel3_b.duty(duty)
            wheel3_f.duty(0)
        
        #wheel4 output
        if(id_ == 4):
            wheel4_f.duty(duty)
            wheel4_b.duty(0)
        if(id_ == -4):
            wheel4_b.duty(duty)
            wheel4_f.duty(0)