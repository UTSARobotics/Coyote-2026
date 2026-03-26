#Importing the GPIO Raspberry Pi4 library
import RPi.GPIO as GPIO
import math
import time


if (__name__ == '__main__'):
    #Setting the numbering of the Raspberry Pi4 pins
    #BOARD refers to the physical pin number pin1 pin2 pin3 ... pin40
    #BCM refers to the channel numbers in diagram GPIO1 GPIO3 GPIO26 so on
    GPIO.setmode(GPIO.BOARD)



    #Setting Physical pins or GPIO17 too outout
    # in1 in2
    # 0   0  Brale or coast
    # 1   0  rotate forward
    # 0   1  rotate reverse
    # 1   1  brake (short brake)
    #JOINT 1
    GPIO.setup(11,GPIO.OUT,initial=GPIO.LOW) #RIGHT
    GPIO.setup(13,GPIO.OUT,initial=GPIO.LOW) #LEFT
    
    #JOINT 2
    GPIO.setup(31,GPIO.OUT,initial=GPIO.LOW) #DOWN
    GPIO.setup(29,GPIO.OUT,initial=GPIO.LOW) #UP
    
    #JOINT 3
    GPIO.setup(16,GPIO.OUT,initial=GPIO.LOW) #UP
    GPIO.setup(18,GPIO.OUT,initial=GPIO.LOW) #DOWN


    
    
    #picking up tool. start poisition is bottom right
    '''print("GO")
    GPIO.output(13,1)
    GPIO.output(11,0)
    print("LEFT")
    time.sleep(3)
    GPIO.output(31,0)
    GPIO.output(13,0)
    GPIO.output(29,1)
    print("UP")
    time.sleep(40)
    GPIO.output(29,0)
    GPIO.output(16,1)
    print("STRAIGHT UP")
    time.sleep(20)
    GPIO.output(16,0)
    print("STOP")'''

    #typing on keyboard. start position is centered up but joing 3 is down
    time.sleep(5)
    GPIO.output(29,0)
    GPIO.output(31,1)
    print("DOWN")
    time.sleep(28)
    GPIO.output(29,0)
    GPIO.output(31,0)
    GPIO.output(11,0)
    GPIO.output(13,1)
    time.sleep(2)
    print("TYPING")
    GPIO.output(11,0)
    GPIO.output(13,0)
    GPIO.output(29,0)
    GPIO.output(31,1)
    time.sleep(2)
    GPIO.output(29,1)
    GPIO.output(31,0)
    time.sleep(6)
    GPIO.output(11,1)
    GPIO.output(13,0)
    time.sleep(3)
    print("TYPING")
    GPIO.output(11,0)
    GPIO.output(13,0)
    GPIO.output(29,0)
    GPIO.output(31,1)
    time.sleep(3)
    GPIO.output(29,1)
    GPIO.output(31,0)
    GPIO.output(11,0)
    GPIO.output(13,1)
    time.sleep(6)
    print("UP")
    GPIO.output(11,0)
    GPIO.output(13,0)
    GPIO.output(29,1)
    GPIO.output(31,0)
    time.sleep(30)
    GPIO.output(29,0)
    GPIO.output(31,0)
    
    




