import tkinter as tk
import socket
import threading
import asyncio
import websockets

# Configuration
BEYOND_IP = "169.254.124.28"  # IP of the PC running BEYOND
#BEYOND_IP = "127.0.0.1"
BEYOND_PORT = 16063  # Correct TCP/IP Talk Server port
LISTEN_PORT = 8000  # Port to receive commands from Digistar

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
    path = playlists[name]
    send_command(f'LoadPlaylist "{path}"')
    send_command("PlayListPlay")

def send_custom_command():
    command = custom_command_entry.get()
    send_command(command)

# Logging incoming Digistar commands
async def handle_client(websocket, path):
    log_message(f"Connection from Digistar at {path}")
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
        log_message(f"[ERROR] Digistar client error: {e}")

async def start_websocket_server():
    server = await websockets.serve(handle_client, "0.0.0.0", LISTEN_PORT)
    log_message(f"[INFO] Listening for Digistar on port {LISTEN_PORT}")
    await server.wait_closed()

def start_listening():
    asyncio.run(start_websocket_server())

# Start listening in a separate thread
threading.Thread(target=start_listening, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("BEYOND Remote Control")
root.geometry("500x600")

output_text = tk.Text(root, height=15, width=60)
output_text.pack(pady=5)

def log_message(message):
    output_text.insert(tk.END, message + "\n")
    output_text.see(tk.END)

# Control Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="▶️ Start Playlist", command=start_playlist, width=20).grid(row=0, column=0, padx=5, pady=5)
tk.Button(button_frame, text="⏸ Pause Playlist", command=pause_playlist, width=20).grid(row=1, column=0, padx=5, pady=5)
tk.Button(button_frame, text="⏹ Stop Playlist", command=stop_playlist, width=20).grid(row=2, column=0, padx=5, pady=5)

# Playlist Buttons
for index, name in enumerate(playlists.keys()):
    tk.Button(button_frame, text=f"Load {name} Playlist", command=lambda n=name: load_playlist(n), width=20).grid(row=0 + index, column=1, padx=5, pady=5)

# Custom Command Entry
custom_command_entry = tk.Entry(root, width=40)
custom_command_entry.pack(pady=5)
tk.Button(root, text="Send Custom Command", command=send_custom_command).pack(pady=5)

root.mainloop()
