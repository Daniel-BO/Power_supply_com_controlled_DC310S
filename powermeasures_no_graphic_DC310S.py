import serial
import csv
import time
from datetime import datetime

# === Configuration ===
SERIAL_PORT = '/dev/ttyUSB0'         # Change for your OS, e.g., '/dev/ttyUSB0'
BAUD_RATE = 115200
TIMEOUT = 1                  # seconds
LOG_FILE = 'power_supply_log.csv'
MEASURE_INTERVAL = 1         # seconds between measurements

# === SCPI Commands in hex ===
COMMANDS = {
    'idn': b'*IDN?\n',
    'output_on': bytes.fromhex('3A4F555450204F4E0A0A0A'),#OUTP ON
    'output_off': bytes.fromhex('3A4F555450204F46460A0A'),
    'meas_voltage': b'MEAS:VOLT?\n',
    'meas_current': b'MEAS:CURR?\n',
    'meas_power': b'MEAS:POW?\n',
}




def initialize_serial(port, baudrate, timeout):
    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"Connected to {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error: {e}")
        return None

def send_command(ser, cmd_bytes):
    ser.write(cmd_bytes)
    time.sleep(0.1)  # Short wait for device to respond
    response = ser.read_all().decode(errors='ignore').strip()
    return response

def apply_voltage_current(ser, voltage, current, protection):
	apply_volt = f":VOLT {voltage}\n\n".encode()
	apply_current = f"CURR: {current}\n\n".encode()
	protect_cmd = f":CURR:PROT {protection}\n\n".encode()
	ser.write(apply_volt)
	time.sleep(0.1)
	ser.write(apply_current)
	time.sleep(0.1)     
	ser.write(protect_cmd)
	print("Settings applied.")
def log_to_csv(timestamp, signal , voltage, current, power):
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, signal, voltage, current, power])

def main():
    Test_cases={"VCC":5,"VCCIN":5,"V3_3V":3.3,"V12V":12}
    ser = initialize_serial(SERIAL_PORT, BAUD_RATE, TIMEOUT)
    if not ser:
        return

    # Create CSV header
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Signal_Tested','Voltage (V)', 'Current (A)', 'Power (W)'])

    try:
       for signal, value in Test_cases.items():
            print(signal, value)
            current_s=6
            protection_1=5
            send_command(ser, COMMANDS['output_off'])
            time.sleep(0.5)       
            apply_voltage_current(ser,value, current_s, protection_1)
            time.sleep(1)
            send_command(ser, COMMANDS['output_on'])
            time.sleep(2)
            
            print(" Da un enter para logear la senal")
            input()
            timestamp = datetime.now().isoformat()
            signal_tested = signal
            voltage = send_command(ser, COMMANDS['meas_voltage'])
            current = send_command(ser, COMMANDS['meas_current'])
            power = send_command(ser, COMMANDS['meas_power'])
            print(f"[{timestamp}] signal:{signal} V: {voltage}, A: {current}, W: {power}")
            log_to_csv(timestamp, signal, voltage, current, power)

            time.sleep(MEASURE_INTERVAL)
            send_command(ser, COMMANDS['output_off'])
            time.sleep(0.5)     
    except KeyboardInterrupt:
        print("Stopped by user.")
        send_command(ser, COMMANDS['output_off'])
    finally:
        ser.close()

if __name__ == '__main__':
    main()
