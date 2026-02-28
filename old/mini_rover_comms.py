import os
import time
import serial
# ros libraries
import rclpy
from rclpy.node import Node
# ros msgs
from std_msgs.msg import Int32MultiArray

# rover node
class rover_node(Node):
    
    def __init__(self):
        super().__init__('rover_node')
        
        # Get serial port from environment variable (default /dev/ttyACM1)
        serial_port = os.environ.get("ROVER_SERIAL_PORT", "/dev/ttyACM1")
        
        # serial object to communicate with ESP32
        self.ser = serial.Serial(serial_port, 115200, timeout=1)        
        
        # node subscriber - listens for motor commands from Taranis node
        self.sub = self.create_subscription(
            Int32MultiArray,
            'rover_motor_commands',  # topic name
            self.rover_callback,
            10)
        
        self.get_logger().info(f'Rover node ready - using serial port {serial_port}')
        
    # subscriber callback
    def rover_callback(self, msg):
        
        # msg.data[0] = left_motor (-100 to 100)
        # msg.data[1] = right_motor (-100 to 100)
        left_motor = msg.data[0]
        right_motor = msg.data[1]
        
        # Send to ESP32 as "L,R" string format
        command = f"{left_motor},{right_motor}\n"
        self.ser.write(command.encode('utf-8'))
        
        # Optional: log the command
        self.get_logger().debug(f"Sent to ESP32: L={left_motor}, R={right_motor}")

# main function
def main():
    
    # running the node
    rclpy.init()
    rnode = rover_node()
    rclpy.spin(rnode)
    
    # if spin fails shutdown
    rnode.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
