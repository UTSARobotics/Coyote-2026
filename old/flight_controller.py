from pymavlink import mavutil

# Open MAVLink connection (adjust port/baud if needed)
master = mavutil.mavlink_connection('/dev/tty.usbmodem101', baud=115200)
master.wait_heartbeat()
print("[HEARTBEAT OK]")

# Latest values (start as None)
latest_alt = None
latest_speed = None
latest_ax = latest_ay = latest_az = None
latest_rollrate = latest_pitchrate = latest_yawrate = None
latest_motors = [None] * 4  # motors 1-4 PWM (us)

GRAVITY = 9.81  # m/s² per g

# --- COMMAND FUNCTIONS -------------------------------------------------

def arm():
    """Send ARM command."""
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
        1,  # arm
        0, 0, 0, 0, 0, 0
    )
    print("[ARM SENT]")

def disarm():
    """Send DISARM command."""
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
        0,  # disarm
        0, 0, 0, 0, 0, 0
    )
    print("[DISARM SENT]")

def send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1500):
    """Send RC override (PWM values 1000-2000 us)."""
    master.mav.rc_channels_override_send(
        master.target_system, master.target_component,
        roll, pitch, throttle, yaw, 0, 0, 0, 0
    )
    print(f"[RC OVERRIDE] roll={roll} pitch={pitch} thr={throttle} yaw={yaw}")

# --- MAIN LOOP ---------------------------------------------------------

try:
    while True:
        msg = master.recv_match(blocking=True)
        if not msg:
            continue

        mtype = msg.get_type()

        # Altitude and ground speed from VFR_HUD
        if mtype == 'VFR_HUD':
            latest_alt = msg.alt
            latest_speed = msg.groundspeed
            print(
                f"Alt: {latest_alt if latest_alt is not None else float('nan'):5.2f} m  "
                f"Speed: {latest_speed if latest_speed is not None else float('nan'):5.3f} m/s  "
            )

        # Linear acceleration from RAW_IMU (milli-g -> m/s²)
        elif mtype == 'RAW_IMU':
            latest_ax = msg.xacc * GRAVITY / 1000.0
            latest_ay = msg.yacc * GRAVITY / 1000.0
            latest_az = msg.zacc * GRAVITY / 1000.0
            print(
                f"aX: {latest_ax if latest_ax is not None else 0:7.3f} m/s²  "
                f"aY: {latest_ay if latest_ay is not None else 0:7.3f} m/s²  "
                f"aZ: {latest_az if latest_az is not None else 0:7.3f} m/s²  "
            )

        # Angular rates from ATTITUDE (rad/s)
        elif mtype == 'ATTITUDE':
            latest_rollrate = msg.rollspeed
            latest_pitchrate = msg.pitchspeed
            latest_yawrate = msg.yawspeed
            print(
                f"p_dot: {latest_rollrate if latest_rollrate is not None else float('nan'): .5f} rad/s  "
                f"q_dot: {latest_pitchrate if latest_pitchrate is not None else float('nan'): .5f} rad/s  "
                f"r_dot: {latest_yawrate if latest_yawrate is not None else float('nan'): .5f} rad/s"
            )

        # Motor PWM values from SERVO_OUTPUT_RAW (microseconds)
        elif mtype == 'SERVO_OUTPUT_RAW':
            latest_motors[0] = msg.servo1_raw
            latest_motors[1] = msg.servo2_raw
            latest_motors[2] = msg.servo3_raw
            latest_motors[3] = msg.servo4_raw
            print(
                f"M1: {latest_motors[0] if latest_motors[0] is not None else 0:4d} "
                f"M2: {latest_motors[1] if latest_motors[1] is not None else 0:4d} "
                f"M3: {latest_motors[2] if latest_motors[2] is not None else 0:4d} "
                f"M4: {latest_motors[3] if latest_motors[3] is not None else 0:4d} us"
            )

        # --- SEND COMMANDS (uncomment one to test) ---
        #arm()           # ARM the vehicle
        # disarm()        # DISARM the vehicle
        #send_rc(1600, 1500, 1600, 1500)  # roll, pitch, throttle, yaw

except KeyboardInterrupt:
    master.close()
    print("[MAVLink connection CLOSED]")

