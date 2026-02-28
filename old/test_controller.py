from evdev import InputDevice, ecodes
import serial

try:
    esp32 = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
except:
    print("ESP32 not found on ACM0, try USB0")
    esp32 = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)

dev = InputDevice('/dev/input/event2') 

throttle = 0  # Speed
steering = 0  # Direction

print("Taranis Tank Control Active...")

for event in dev.read_loop():
    if event.type == ecodes.EV_ABS:
        # Update values based on stick movement
        if event.code == ecodes.ABS_X:      # Left Stick
            throttle = event.value
        elif event.code == ecodes.ABS_Y:    # Right Stick
            steering = event.value

        # --- TANK MIXING MATH ---
        # 1. Normalize values (assuming 0-255 range, 128 is center)
        # We want a range of -100 to +100
        v = (throttle - 128) * -0.78  # Speed (Inverted so Up is positive)
        w = (steering - 128) * 0.78   # Turn

        # 2. Calculate individual side speeds
        left_motor = int(v + w)
        right_motor = int(v - w)

        # 3. Constrain to -100 to 100 range
        left_motor = max(min(left_motor, 100), -100)
        right_motor = max(min(right_motor, 100), -100)

        # 4. Send to ESP32 as "L,R" string
        command = f"{left_motor},{right_motor}\n"
        esp32.write(command.encode())

        print(f"L: {left_motor} | R: {right_motor}")
