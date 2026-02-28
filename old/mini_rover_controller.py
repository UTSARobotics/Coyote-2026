import rclpy
from rclpy.node import Node
from evdev import InputDevice, ecodes
import serial
from std_msgs.msg import Int32MultiArray


class radio_game_controller_node(Node):

      def __init__(self):
         super().__init__('rover_radio_game_controller')
         self.pub = self.create_publisher(Int32MultiArray, '/rover_tweet', 10)

         dev = InputDevice('/dev/input/event4')   
         
         # Speed 
         throttle = 0  # Speed
         steering = 0  # Direction

         # listen to input from the evdev
         for event in dev.read_loop():
            if event.type == ecodes.EV_ABS:
            # Update values based on stick movement
               if event.code == ecodes.ABS_X:      # Left Stick
                  throttle = event.value
               elif event.code == ecodes.ABS_Y:    # Right Stick
                  steering = event.value

               # --- TANK MIXING MATH ---
               # TODO: Fix these comments
               # 1. Normalize values (assuming 0-255 range, 128 is center)
               # We want a range of -100 to +100
               v = (throttle - 1024) / -10.24  # Speed (Inverted so Up is positive)
               w = (steering - 1024) / 10.24  # Turn

               # 2. Calculate individual side speeds
               left_motor = int(v + w)
               right_motor = int(v - w)

               # 3. Constrain to -100 to 100 range
               left_motor = max(min(left_motor, 100), -100)
               right_motor = max(min(right_motor, 100), -100)

               # 4. Send to ESP32 as "L,R" string
               command = f"{left_motor},{right_motor}\n"

               print(f"L: {left_motor} | R: {right_motor}")


# main function
def main():
    
    # running the node
    rclpy.init()
    rover_radio_game_controller = radio_game_controller_node()
    rclpy.spin(radio_game_controller)
    
    # if spin fails shutdown
    rover_radio_game_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
