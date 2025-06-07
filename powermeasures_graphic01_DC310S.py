import serial
import csv
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# === Configuration ===
SERIAL_PORT = '/dev/ttyUSB0'       # Set accordingly
BAUD_RATE = 115200
TIMEOUT = 1
LOG_FILE = 'power_log.csv'
MEASURE_INTERVAL = 2       # Seconds

# === SCPI Hex Commands ===
COMMANDS = {
    'idn': b'*IDN?\n',
    'output_on': bytes.fromhex('3A4F555450204F4E0A0A0A0A'),
    'output_off': bytes.fromhex('3A4F555450204F46460A0A'),
    'meas_voltage': b'MEAS:VOLT?\n',
    'meas_current': b'MEAS:CURR?\n',
    'meas_power': b'MEAS:POW?\n',
}

class PowerSupplyGUI:
    def __init__(self, root):
        self.ser = None
        self.running = False
        self.thread = None

        self.root = root
        self.root.title("Power Supply DC310S Control Panel")

        self.voltage_var = tk.StringVar(value="5")
        self.current_var = tk.StringVar(value="1")
        self.protect_var = tk.StringVar(value="6")

        self.meas_voltage = tk.StringVar(value="0")
        self.meas_current = tk.StringVar(value="0")
        self.meas_power = tk.StringVar(value="0")

        self.build_gui()

    def build_gui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid()

        # Input settings
        ttk.Label(frame, text="Voltage (V):").grid(column=0, row=0, sticky='e')
        ttk.Entry(frame, textvariable=self.voltage_var).grid(column=1, row=0)
        ttk.Label(frame, text="Current (A):").grid(column=0, row=1, sticky='e')
        ttk.Entry(frame, textvariable=self.current_var).grid(column=1, row=1)
        ttk.Label(frame, text="Protection Current (A):").grid(column=0, row=2, sticky='e')
        ttk.Entry(frame, textvariable=self.protect_var).grid(column=1, row=2)

        # Buttons
        ttk.Button(frame, text="Connect", command=self.connect_serial).grid(column=0, row=3)
        ttk.Button(frame, text="Apply Settings", command=self.apply_settings).grid(column=1, row=3)
        ttk.Button(frame, text="Output ON", command=self.output_on).grid(column=0, row=4)
        ttk.Button(frame, text="Output OFF", command=self.output_off).grid(column=1, row=4)
        ttk.Button(frame, text="Start Logging", command=self.start_logging).grid(column=0, row=5)
        ttk.Button(frame, text="Stop Logging", command=self.stop_logging).grid(column=1, row=5)

        # Measurement display
        ttk.Label(frame, text="Voltage (V):").grid(column=0, row=6)
        ttk.Label(frame, textvariable=self.meas_voltage).grid(column=1, row=6)
        ttk.Label(frame, text="Current (A):").grid(column=0, row=7)
        ttk.Label(frame, textvariable=self.meas_current).grid(column=1, row=7)
        ttk.Label(frame, text="Power (W):").grid(column=0, row=8)
        ttk.Label(frame, textvariable=self.meas_power).grid(column=1, row=8)

    def connect_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
            print("Connected to serial.")
        except serial.SerialException as e:
            print(f"Serial error: {e}")

    def send_command(self, cmd):
        if not self.ser:
            print("Serial not connected.")
            return ""
        self.ser.write(cmd)
        time.sleep(0.1)
        return self.ser.read_all().decode(errors='ignore').strip()

    def apply_settings(self):
        voltage = self.voltage_var.get()
        current = self.current_var.get()
        prot = self.protect_var.get()

        apply_volt = f":VOLT {voltage}\n\n".encode()
        apply_current = f"CURR: {current}\n\n".encode()
        protect_cmd = f":CURR:PROT {prot}\n\n".encode()

        self.ser.write(apply_volt)
        time.sleep(0.1)
        self.ser.write(apply_current)
        time.sleep(0.1)
        
        self.ser.write(protect_cmd)
        print("Settings applied.")

    def output_on(self):
        self.send_command(COMMANDS['output_on'])
        print("Output ON.")
        print(COMMANDS['output_on'])

    def output_off(self):
        self.send_command(COMMANDS['output_off'])
        print("Output OFF.")

    def start_logging(self):
        if not self.running:
            self.running = True
            with open(LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Voltage (V)", "Current (A)", "Power (W)"])
            self.thread = threading.Thread(target=self.measure_loop, daemon=True)
            self.thread.start()
            print("Logging started.")

    def stop_logging(self):
        self.running = False
        print("Logging stopped.")

    def measure_loop(self):
        while self.running:
            try:
                voltage = self.send_command(COMMANDS['meas_voltage'])
                current = self.send_command(COMMANDS['meas_current'])
                power = self.send_command(COMMANDS['meas_power'])

                timestamp = datetime.now().isoformat()
                self.meas_voltage.set(voltage)
                self.meas_current.set(current)
                self.meas_power.set(power)

                with open(LOG_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([timestamp, voltage, current, power])

                time.sleep(MEASURE_INTERVAL)
            except Exception as e:
                print(f"Error during logging: {e}")
                self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = PowerSupplyGUI(root)
    root.mainloop()
