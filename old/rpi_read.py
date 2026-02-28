from machine import Pin, UART
import time

uart = UART(2, baudrate=420000, bits=8, parity=None, stop=1, rx=27, tx=16)

def read_ghost_data():
    if uart.any():
        data = uart.read()

        if data and len(data) >= 4:  # minimum frame size
            address = data[0]
            length = data[1]
            msg_type = data[2]

            # Make sure full frame arrived
            if len(data) >= (3 + length + 1):
                payload = data[3:3+length]
                crc = data[3+length]

                print("Payload:", payload)
            else:
                print("Incomplete frame")

while True:
    read_ghost_data()
    time.sleep_ms(10)
