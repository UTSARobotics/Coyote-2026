from machine import UART, PWM, Pin
import time

# ---------------------------
# Hardware Setup
# ---------------------------
motor_left  = PWM(Pin(18), freq=50)
motor_right = PWM(Pin(19), freq=50)

uart = UART(2, baudrate=420000, bits=8, parity=None, stop=1, rx=16, tx=17)

# ---------------------------
# ESC Control
# ---------------------------
def set_us(microseconds, motor):
    microseconds = max(1000, min(2000, microseconds))
    motor.duty_ns(microseconds * 1000)

def arm_escs():
    print("arming")
    set_us(1450, motor_left)
    set_us(1450, motor_right)
    time.sleep(10)
    print("armed")

# ---------------------------
# Channel Mapping
# ---------------------------
IN_MIN  = 346
IN_MAX  = 3622
CENTER  = (IN_MIN + IN_MAX) // 2
DEADBAND = 40

def map_channel(raw):
    raw = max(IN_MIN, min(IN_MAX, raw))
    value = (raw - CENTER) / (IN_MAX - IN_MIN)
    return value * 2  # roughly -1 to +1

# ---------------------------
# Differential Mixing
# ---------------------------
def drive(throttle_raw, steering_raw):

    throttle = map_channel(throttle_raw)
    steering = map_channel(steering_raw)

    # Deadband
    if abs(throttle) < 0.05:
        throttle = 0
    if abs(steering) < 0.05:
        steering = 0

    left  = throttle + steering
    right = throttle - steering

    # Normalize
    max_mag = max(abs(left), abs(right), 1)
    left  /= max_mag
    right /= max_mag

    left_pulse  = int(1460 + left * 200)
    right_pulse = int(1460 + right  * 200)

    set_us(left_pulse, motor_left)
    set_us(right_pulse, motor_right)
    print(left_pulse)
    print(right_pulse)

# CRC8 DVB-S2
def crc8_dvb_s2(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


buffer = bytearray()
    
    

def parse_ghst():
    global buffer

    if uart.any():
        buffer.extend(uart.read())

    while len(buffer) >= 4:  # minimum: addr + len + type + crc
        addr = buffer[0]
        length = buffer[1]

        full_frame_len = 2 + length

        if len(buffer) < full_frame_len:
            return  # wait for more bytes

        frame = buffer[:full_frame_len]
        buffer = buffer[full_frame_len:]

        # Now based on your structure:
        # [ADDR][LEN][TYPE][PAYLOAD...][CRC]

        frame_type = frame[2]
        received_crc = frame[-1]

        # CRC calculated over TYPE + PAYLOAD (NOT including CRC)
        calculated_crc = crc8_dvb_s2(frame[2:-1])

        if calculated_crc != received_crc:
            print("CRC FAIL")
            buffer = []
            continue

        payload = frame[3:-1]  # isolate payload cleanly

        print("Valid Frame")
        print("Type:", frame_type)
        print("Payload:", [p for p in payload])

        # Example: decode first 4 channels if enough payload
        if len(payload) >= 6:
            ch1 = (payload[0] | (payload[1] << 8)) & 0x0FFF
            ch2 = ((payload[1] >> 4) | (payload[2] << 4)) & 0x0FFF
            ch3 = (payload[3] | (payload[4] << 8)) & 0x0FFF
            ch4 = ((payload[4] >> 4) | (payload[5] << 4)) & 0x0FFF

            print("CH1:", ch1, "CH2:", ch2, "CH3:", ch3, "CH4:", ch4)
            drive(ch1, ch2)
            
# ---------------------------
# Main
# ---------------------------
arm_escs()

while True:
    
    parse_ghst()