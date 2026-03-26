import RPi.GPIO as GPIO
import time
from gpiozero import PWMLED


def main():
	#pwm object created
	led = PWMLED(13)
	
	#acceptable range 0.02 too 0.22 (servo responds)
	while(True):
		i = float(input("Duty Cycle: "))
		led.value = i
		time.sleep(1)
	
	
if(__name__=='__main__'):
	main()
