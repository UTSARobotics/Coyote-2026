from machine import UART, PWM, Pin
import time

servo = PWM(Pin(19), freq=50)
uart = UART(2, baudrate=420000, bits=8, parity=None, stop=1, rx=16, tx=17)

def set_angle(angle):
    duty = int((angle / 180) * (125-20) +20)
    servo.duty(duty)




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
            set_angle(90)


            while ch1 > 346:
                print("fuck")
                qwerty = (ch1 - 346) / (3622 - 346) * 180
                set_angle(qwerty)
                time.sleep_ms(100)


            if ch4 > 2000:
                print("FUCK")
                set_angle(180)


while True:
    parse_ghst()
    time.sleep_ms(2)
