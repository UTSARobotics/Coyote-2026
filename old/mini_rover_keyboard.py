import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from pynput import keyboard


class keyboard_node(Node):

    def __init__(self):
        super().__init__('rover_keyboard')
        self.pub = self.create_publisher(Int32MultiArray, '/rover_tweet', 10)
        #keyboard listener
        listener = keyboard.Listener(on_press=self.on_press)
        listener.daemon = True
        listener.start()
        #speed
        self.left_speed = 0
        self.right_speed = 0
        
    #function that detects keyboard presses
    def on_press(self, key):
        try:
           if(key.char == 'w'):
              print("left_speed: "+str(self.left_speed) + "     " + "\r")
              #left speed tweet1
              msg1 =Int32MultiArray()
              msg2 = Int32MultiArray()
              if(self.left_speed < 1000):
                 self.left_speed = self.left_speed + 100
              if(self.left_speed >= 0):
                 msg1.data = [1,self.left_speed]
                 msg2.data = [2,self.left_speed]
              else:
                 msg1.data = [-1,abs(self.left_speed)]
                 msg2.data = [-2,abs(self.left_speed)]
              self.pub.publish(msg1)
              self.pub.publish(msg2)
       	   if(key.char == 's'):
              print("left_speed: "+str(self.left_speed) + "     " + "\r")
              #left speed tweet2
              msg1 =Int32MultiArray()
              msg2 = Int32MultiArray()
              if(self.left_speed > -1000):
                self.left_speed = self.left_speed - 100
              if(self.left_speed >= 0):
                 msg1.data = [1,self.left_speed]
                 msg2.data = [2,self.left_speed]
              else:
                 msg1.data = [-1,abs(self.left_speed)]
                 msg2.data = [-2,abs(self.left_speed)]
              self.pub.publish(msg1)
              self.pub.publish(msg2)
          
          
           if(key.char == 'e'):
               print("right_speed: "+str(self.right_speed) + "     " + "\r")
               #right speed tweet1
               msg1 =Int32MultiArray()
               msg2 = Int32MultiArray()
               if(self.right_speed < 1000):
                  self.right_speed = self.right_speed + 100
               if(self.right_speed >= 0):
                  msg1.data = [3,self.right_speed]
                  msg2.data = [4,self.right_speed]
               else:
                  msg1.data = [-3,abs(self.right_speed)]
                  msg2.data = [-4,abs(self.right_speed)]
               self.pub.publish(msg1)
               self.pub.publish(msg2)
       	   if(key.char == 'd'):
              print("right_speed: "+str(self.right_speed) + "     " + "\r")
              #right speed tweet1
              msg1 =Int32MultiArray()
              msg2 = Int32MultiArray()
              if(self.right_speed > -1000):
                 self.right_speed = self.right_speed - 100
              if(self.right_speed >= 0):
                 msg1.data = [3,self.right_speed]
                 msg2.data = [4,self.right_speed]
              else:
                 msg1.data = [-3,abs(self.right_speed)]
                 msg2.data = [-4,abs(self.right_speed)]
              self.pub.publish(msg1)
              self.pub.publish(msg2)
              
       	   		
        except AttributeError:
           # non-character keys don't have .char
           pass

        
           


def main(args=None):

    #keyboard node
    rclpy.init(args=args)
    keyboard = keyboard_node()
    rclpy.spin(keyboard)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

