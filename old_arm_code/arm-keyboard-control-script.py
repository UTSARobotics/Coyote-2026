#pynput library for mointoring keyboard
from pynput import keyboard

#Importing the GPIO Raspberry Pi4 library adn gpio zero library
import RPi.GPIO as GPIO
import math
import time

#gpiozero imports
from gpiozero import PWMLED
from gpiozero.pins.pigpio import PiGPIOFactory

#Setting pin numbering too Board
GPIO.setmode(GPIO.BOARD)

#Setting physical pin 11 and 13 too Outputs and initial LOW or 0v
GPIO.setup(11,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(13,GPIO.OUT,initial=GPIO.LOW)

#Setting up the physical pin 29 and 31 too Outputs and initial Low or 0v
GPIO.setup(29,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(31,GPIO.OUT,initial=GPIO.LOW)

#Setting up the physical pin 16 and 18 too Outputs and initial Low or 0v
GPIO.setup(16,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(18,GPIO.OUT,initial=GPIO.LOW)

#Setting up led object from gpiozero library for joint 4-gripper, initial open, uses pigpio factory for pwm generation
factory = PiGPIOFactory()
gripper = PWMLED(13,pin_factory=factory)
gripper.value = 0.20

#callback function for listener when key is pressed
def on_press(key):
    
    #checking for joint 1 keys
    if(hasattr(key,'char') and key.char == 'q'):
        print("Joint1 CCW     ", end='\r')
        #setting gpio pins for ccw
        GPIO.output(13,0)
        GPIO.output(11,1)
        
    elif(hasattr(key,'char') and key.char =='a'):
        print("Joint1 CW      ", end='\r')
        #setting gpio pins for cw
        GPIO.output(11,0)
        GPIO.output(13,1)
        
    #checking for joint 2 keys
    elif(hasattr(key,'char') and key.char=='w'):
    	print("Joint2 UP      ", end='\r')
    	#setting up gpio pins for UP
    	GPIO.output(29,1)
    	GPIO.output(31,0)
    elif(hasattr(key,'char') and key.char=='s'):
    	print("Joint2 DOWN    ", end='\r')
    	#setting up gpio pins for DOWN
    	GPIO.output(29,0)
    	GPIO.output(31,1)
    
    
    #checking for joint3 keys
    elif(hasattr(key,'char') and key.char=='e'):
    	print("Joint3 UP      ", end='\r')
    	#setting up gpio pins for UP
    	GPIO.output(16,1)
    	GPIO.output(18,0)
    	
    elif(hasattr(key,'char') and key.char == 'd'):
    	print("Joint 3 DOWN   ", end='\r')
    	#setting up gpio pins for DOWN
    	GPIO.output(16,0)
    	GPIO.output(18,1)
    	
    #checking for join4-gripper keys
    elif(hasattr(key,'char') and key.char == 'r'):
    	print("Joint 4 CLOSE   ", end='\r')
    	#setting gpio pin 13 pwm
    	gripper.value = 0.10
    elif(hasattr(key,'char') and key.char == 'f'):
    	print("Joint 4 OPEN    ", end='\r')
    	#setting gpio pin 13 pwm
    	gripper.value = 0.20
    else:
    	print("STOP          ",end='\r')
    	#setting up gpio pins for STOP
    	
    	#joint1
    	GPIO.output(11,0)
    	GPIO.output(13,0)
    	#joint2
    	GPIO.output(29,0)
    	GPIO.output(31,0)
    	#joint3
    	GPIO.output(16,0)
    	GPIO.output(18,0)
    	#joint4 no change
    

#creating a listener object too monitor keyboard
listener = keyboard.Listener(on_press=on_press)
listener.start()

if (__name__ == '__main__'):
    print("Q/A for joint 1")
    print("W/S for joint 2")
    print("E/D for joint 3")
    print("R/F for gripper")
    print("All other keys STOP")
    
    while(True):
        pass
