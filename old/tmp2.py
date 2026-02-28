from machine import UART, PWM, Pin
import time

servo = PWM(Pin(19), freq=50)
uart = UART(2, baudrate=420000, bits=8, parity=None, stop=1, rx=16, tx=17)

def set_angle(angle):
    duty = int((angle / 180) * (125-20) +20)
    servo.duty(duty)


def steering_control(anglech2):
    if ch2 == (1984 or 1986):
        anglech2 = 0
    else:
        if ch2 > 1984:
            anglech2 = ((ch2 - 1984) / 1638) * 180
        if ch2 > 1986:
            anglech2 = ((ch2 - 1986) / 1636) * 180
        if ch2 < 1984:
            anglech2 = ((1984 - ch2) / 1638) * -180
        if ch2 < 1986:
            anglech2 = ((1986 - ch2) / 1636) * -180
        set_angle(anglech2)
                    
 
                
                               
                    
                        


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

def get_duty_cycle(raw_value):
        in_min, in_max = 326, 3266
        out_min, out_max = -100, 100
    
        mapped_val = out_min + (raw_value - in_min) * (out_max - out_min) / (in_max - in_min)
    
        duty = ((mapped_val + 100) / 200) * 5
        
        print(int(duty))
        return int(duty)
    
    

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
            
            #target_duty = get_duty_cycle(ch1)
            
            if ch1 > 3000 and ch4 > 2000:
                set_angle(0)   # backwards
            if ch1 > 3000 and ch4 < 2000:
                set_angle(180) # forward
            if ch1 > 1000 and ch1 < 3000:
                set_angle(90)  # Still
                
                
            steering_control(ch2)
            
            #qwerty = (ch1 - 346) / (3622 - 346) * 180
            #set_angle(qwerty)
            #time.sleep_ms(100)

            #if ch4 > 2000:
            #    print("FUCK")
            #    set_angle(180)

            
while True:
    parse_ghst()
    time.sleep_ms(2)