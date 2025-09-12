

'''

First iteration of scan on a sample. This scan's structure must be something of the kind:
- Initiate necessary devices in correct order with hardcoded addresses
- Create data structure for measurements, which is a list with positions and counts

- Create a step list in sequence, which means a list populated by the values in which the nanopositioner will have to step on.
- The nanopositioner then zeroes it's position
- Sets a velocity
- The timecontroller records count and DataCount object has a time and frequency information.

'''
from devices.idq_tc1000_counter import *
from devices.idq_tc1000_device import *
from devices.montana_cryoadvance_controls import *
from scans import scan_data_structures
from utils.common import connect
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import time
import signal
import sys




# Connections section

tc = connect("149.132.99.103")   # Connection for IDQ
montana_ip = "149.132.99.104"


# Preparation of IDQ TC
try:
    timecontroller = TimeController(tc)
    start_counter = TCCounter(tc, "start")
    input1_counter = TCCounter(tc, 1)

    for i in ["start", 1]:
        timecontroller.enable_input(i)

except Exception as e:
    print(f"Error during preparation of IDQ: {e}")

print(f'Threshold on Start: {timecontroller.threshold("start")}\nThreshold on Input 1: {timecontroller.threshold(1)}\n')

# Preparation of Montana:
try:
    positioner = Positioner(montana_ip)

except Exception as e:
    print(f"Error during preparation of Montana: {e}")

# Operational Parameters:

scan_set = ScanParameters()

scan_set.step_size["Z"]=10e-6   # metres
scan_set.step_velocity=50 * 1e-6    # meters/sec  ##IMPLEMENT THIS IN THE POSITIONER CLASS. doing it manually from screen
scan_set.resolution["Z"]=250
scan_set.polling_frequency=100 #HZ to update positioner status

# Mechanisms:

#Preparation of Data Structures 

Y_DATA = []
X_DATA = []

for i in range(0, step_count):
    Y_DATA.append(0)
    X_DATA.append(0)

def scan_routine(step_index, step_list, x_data_list, y_data_list, counter, positioner, axis):

    def wait_end_motion():
        start=time.time()
        
        while True:
            if positioner.status(axis)["moving"] == False:
                break
            time.sleep(1/polling_frequency)
        
        end=time.time()
        print(f"Waited for motion {(end-start)*1000} mS")
        return

    print(f"Step: {step_index}")    
    
    actual_position=positioner.status(axis)["theoreticalPosition"]

    x_data_list[step_index] = actual_position       ## Record X step with feedback from positioner.

    y_data_list[step_index] = counter.count().frequency() # Record Y value from counter frequency

    positioner.move_to_position(axis, step_list[step_index])

    wait_end_motion()

    time.sleep(0.2)






def exit():
    print("Received signal to stop.")
    positioner.stop(axis)
    for i in ["start", 1]:
        timecontroller.disable_input(i)
    
    sys.exit(0)


# Emergency Exit:
signal.signal(signal.SIGINT, exit)   # Ctrl+C
signal.signal(signal.SIGTERM, exit)  # kill <pid>


# Main logic:
try:
    print("Tutto pronto. Premi invio...")
    input()

    start_time = time.time()
    positioner.zero_position(axis)

    for step_index in range(0, step_count):
        
        scan_routine(step_index, STEPS, X_DATA, Y_DATA, input1_counter, positioner, axis)

    end_time=time.time()
    print(f"Time Elapsed for Scan: {end_time-start_time} S")

    X_DATA=[round(p * 1e6, 2) for p in X_DATA]

    fig, ax = plt.subplots()
    ax.plot(X_DATA, Y_DATA)
    ax.set_title("1D Scan - 200 x 1 Micrometer Steps", fontsize=14, fontweight="bold")
    ax.set_xlabel("Position (microM)", fontsize=10)
    ax.set_ylabel("Photon incidence frequency (Hz)", fontsize=9)
    ax.xaxis.set_major_locator(MultipleLocator(200))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.grid(True, linestyle="--", alpha=0.6)
    
    plt.savefig("graph.png", dpi=500)


    print("Premi invio per uscire...")
    input()

except Exception as e:
    print(e)
    exit()







