#pynput library for mointoring keyboard
import pynput
from pynput import keyboard


#callback function for listener when key is pressed
def on_press(key):
    
    #checking for joint 1 key
    if(hasattr(key,'char') and key.char == 'q'):
        print("Joint1 CCW     ", end='\r')
        #setting gpio pins for ccw
        
    elif(hasattr(key,'char') and key.char =='a'):
        print("Joint1 CW      ", end='\r')
        #setting gpio pins for cw
    else:
        print("Invalid        ", end="\r")
        #setting gpio pins for stop
    

#creating a listener object too monitor keyboard
listener = keyboard.Listener(on_press=on_press)
listener.start()

if (__name__ == '__main__'):
    print("Q/A for joint 1")
    print("W/S for joint 2")
    print("E/D for joint 3")
    print("All other keys STOP")
    
    while(True):
    	pass
