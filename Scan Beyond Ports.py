import tkinter as tk
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

# TCP/IP Talk Server settings
ip = "127.0.0.1"  # Localhost for BEYOND
scanning = False
completed_ports = 0  # Tracks completed ports

# Function to send a PangoScript command
def send_command(command, port):
    try:
        with socket.create_connection((ip, port), timeout=2) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            if response:
                return f"[RESPONSE] {response}"
            else:
                return "[RESPONSE] (empty)"
    except Exception:
        return None

# Function to scan a single port (for multithreading)
def scan_single_port(port):
    global completed_ports
    response = send_command("HELP", port)
    if response:
        log_open_port(port, response)

    completed_ports += 1  # Track completed ports
    if completed_ports % 100 == 0:
        log_message(f"[INFO] Scanned {completed_ports} ports so far...")

    # Update the current port display (only for completed ports)
    current_port_label.config(text=f"Current Port: {port}")

# Function to scan ports using multithreading
def scan_ports():
    global scanning, completed_ports
    scanning = True
    completed_ports = 0  # Reset counter
    with ThreadPoolExecutor(max_workers=10) as executor:
        for port in range(2600, 10001):
            if not scanning:
                break
            executor.submit(scan_single_port, port)

    log_message("[INFO] Port scanning completed.")

# Function to start port scanning
def start_scan():
    global scanning
    if not scanning:
        log_message("[INFO] Starting port scan from 1 to 10000...")
        open_ports_list.delete(0, tk.END)  # Clear old results
        threading.Thread(target=scan_ports).start()

# Function to stop scanning
def stop_scan():
    global scanning
    scanning = False
    log_message("[INFO] Scan stopped.")

# GUI Setup
root = tk.Tk()
root.title("BEYOND Remote Control App")
root.geometry("400x500")

output_text = tk.Text(root, height=10, width=50)
output_text.pack(pady=5)

current_port_label = tk.Label(root, text="Current Port: Not scanning")
current_port_label.pack()

open_ports_label = tk.Label(root, text="Open Ports:")
open_ports_label.pack()

open_ports_list = tk.Listbox(root, height=10, width=50)
open_ports_list.pack(pady=5)

def log_message(message):
    output_text.insert(tk.END, message + "\n")
    output_text.see(tk.END)

def log_open_port(port, response):
    open_ports_list.insert(tk.END, f"Port {port}: {response}")
    open_ports_list.see(tk.END)

scan_button = tk.Button(root, text="Scan Ports", command=start_scan)
scan_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop Scan", command=stop_scan)
stop_button.pack(pady=5)

root.mainloop()
