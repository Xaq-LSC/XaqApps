from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
import tkinter as tk
import socket
import asyncio
import websockets
import requests
import xml.etree.ElementTree as ET
import time

# Configuration
BEYOND_IP = "192.168.2.19"  # Dome Laser PC
BEYOND_PORT = 16063         # Correct TCP/IP Talk Server port
WEBSOCKET_PORT = 8000       # Port for WebSocket
HTTP_PORT = 8001            # Port for HTTP (cURL)

DIGISTAR_URL = "http://192.168.2.99/software/objects?cached=%2Fsoftware%2Fsite%2Fapps%2Fdigistar%2Fui%2Fcontrolpanel%2Fspacetrip%20-%20xaq.dscp&async=true"
WATCHED_ID = "TextBlock_1a18106149f8d77ab8f"  # Replace with actual ID
POLL_INTERVAL = 2  # seconds

# Playlists paths
playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024',
    "Bad Bunny": r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023',
    "Sabrina Carpenter": r'C:\BEYOND40\Shows\Sabrina Carpenter\Sabrina Carpenter'
}

# Send a command to BEYOND
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            log_message(f"[BEYOND RESPONSE] {response}")
    except Exception as e:
        log_message(f"[ERROR] {e}")

# Command functions
def start_playlist():
    send_command("PlayListPlay")

def stop_playlist():
    send_command("PlayListStop")

def pause_playlist():
    send_command("PlayListPause")

def load_playlist(name):
    if name in playlists:
        path = playlists[name]
        send_command(f'LoadPlaylist "{path}"')
    else:
        log_message(f"[ERROR] Unknown playlist: {name}")

def send_custom_command():
    command = custom_command_entry.get()
    send_command(command)

# Thread-safe logging function
def log_message(message):
    try:
        output_text.after(0, lambda: output_text.insert(tk.END, message + "\n"))
        output_text.after(0, lambda: output_text.see(tk.END))
    except:
        print(message)  # Fallback to console log

# WebSocket Server for Digistar Commands
async def handle_client(websocket, path):
    log_message(f"[WEBSOCKET] Connection from Digistar at {path}")
    try:
        async for message in websocket:
            log_message(f"[DIGISTAR] {message}")
            if message == "Start":
                start_playlist()
            elif message == "Stop":
                stop_playlist()
            elif message == "Pause":
                pause_playlist()
            elif message.startswith("Load"):
                _, name = message.split(" ", 1)
                load_playlist(name)
            else:
                send_command(message)
    except Exception as e:
        log_message(f"[ERROR] WebSocket Error: {e}")

async def start_websocket_server():
    try:
        server = await websockets.serve(handle_client, "0.0.0.0", WEBSOCKET_PORT)
        log_message(f"[INFO] WebSocket server listening on port {WEBSOCKET_PORT}")
        await server.wait_closed()
    except Exception as e:
        log_message(f"[ERROR] WebSocket Server Error: {e}")


def start_http_server():
    try:
        server_address = ('0.0.0.0', HTTP_PORT)
        httpd = HTTPServer(server_address, BeyondHTTPRequestHandler)
        ip = socket.gethostbyname(socket.gethostname())
        log_message(f"[INFO] HTTP Server listening on {ip}:{HTTP_PORT} for cURL commands")
        httpd.serve_forever()
    except Exception as e:
        log_message(f"[ERROR] HTTP Server Error: {e}")

# HTTP Server for cURL Commands
class BeyondHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        log_message(f"[HTTP] Received GET request: {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Beyond App is alive")

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            log_message(f"[HTTP] Received POST command: {post_data}")
            if post_data == "Start":
                start_playlist()
            elif post_data == "Stop":
                stop_playlist()
            elif post_data == "Pause":
                pause_playlist()
            elif post_data.startswith("Load"):
                _, name = post_data.split(" ", 1)
                load_playlist(name)
            else:
                send_command(post_data)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Command received successfully")
        except Exception as e:
            log_message(f"[ERROR] HTTP POST Error: {e}")
            self.send_response(500)
            self.end_headers()

# Digistar polling thread
def poll_digistar():
    last_seen_value = None
    while True:
        try:
            response = requests.get(DIGISTAR_URL, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                for attr in root.findall(".//{http://es.com/digistar/2012/03}DsAttributeValue"):
                    attr_id = attr.find("{http://es.com/digistar/2012/03}Id")
                    value = attr.find("{http://es.com/digistar/2012/03}Value")
                    if attr_id is not None and value is not None:
                        if attr_id.text == WATCHED_ID and value.text != last_seen_value:
                            last_seen_value = value.text
                            log_message(f"[DIGISTAR] {attr_id.text} changed to {value.text}")
                            if value.text == "StartLaserShow":
                                start_playlist()
        except Exception as e:
            log_message(f"[DIGISTAR ERROR] {e}")
        time.sleep(POLL_INTERVAL)

# Start HTTP, WebSocket, and Digistar threads
threading.Thread(target=start_http_server, daemon=True).start()
threading.Thread(target=lambda: asyncio.run(start_websocket_server()), daemon=True).start()
threading.Thread(target=poll_digistar, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("BEYOND Remote Control")
root.geometry("500x600")

output_text = tk.Text(root, height=20, width=60)
output_text.pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="▶️ Start Playlist", command=start_playlist, width=20).grid(row=0, column=0, padx=5, pady=5)
tk.Button(button_frame, text="⏸ Pause Playlist", command=pause_playlist, width=20).grid(row=1, column=0, padx=5, pady=5)
tk.Button(button_frame, text="⏹ Stop Playlist", command=stop_playlist, width=20).grid(row=2, column=0, padx=5, pady=5)

for index, name in enumerate(playlists.keys()):
    tk.Button(button_frame, text=f"Load {name} Playlist", command=lambda n=name: load_playlist(n), width=20).grid(row=0 + index, column=1, padx=5, pady=5)

custom_command_entry = tk.Entry(root, width=40)
custom_command_entry.pack(pady=5)
tk.Button(root, text="Send Custom Command", command=send_custom_command).pack(pady=5)

root.mainloop()
