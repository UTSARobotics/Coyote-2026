import ctypes, os, sys, time

# Load DLL
os.add_dll_directory(r"C:\Program Files (x86)\sweep\lib")
ctypes.cdll.LoadLibrary(r"C:\Program Files (x86)\sweep\lib\libsweep.dll")

# Import sweeppy from source, not site-packages
sys.path.insert(0, r"C:\Users\97450\sweep-sdk\sweeppy")
from sweeppy import Sweep

with Sweep('COM7') as sweep:
    sweep.set_motor_speed(1)
    sweep.set_sample_rate(500)
    time.sleep(4)
    sweep.start_scanning()

    for scan in sweep.get_scans():
        for s in scan.samples:
            angle = s.angle / 1000.0
            dist  = s.distance
            sig   = s.signal_strength
            if dist > 2 and sig > 15:
                print(f"{angle:.2f},{dist},{sig}")