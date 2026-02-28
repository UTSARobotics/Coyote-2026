import serial
import time
import sys

# --- Configuration ---
# Replace 'COM4' with your ESP32's actual port name
port_name = '27' 
# Must match the baud rate set in the Arduino code
baud_rate = 420000 
# Set a timeout for reading
timeout_value = 2 
# ---------------------

try:
    # Initialize the serial connection
    ser = serial.Serial(port_name, baudrate=baud_rate, timeout=timeout_value)
    time.sleep(2) # Give the connection time to establish
    print(f"Serial port {port_name} opened successfully.")

    while True:
        # Read a line of data ending with a newline character
        value = ser.readline()
        if value:
            # Decode the bytes received from the serial port into a UTF-8 string
            line = str(value, encoding="UTF-8").strip() 
            print(f"Received: {line}")

except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("Exiting program...")
finally:
    if 'ser' in locals() and ser.isOpen():
        ser.close()
        print("Serial port closed.")

