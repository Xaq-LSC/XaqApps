
import asyncio
import nest_asyncio
import socket
import xml.etree.ElementTree as ET
from datetime import datetime
from tkinter import Tk, scrolledtext, ttk

from playwright.async_api import async_playwright

nest_asyncio.apply()

# BEYOND configuration
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024',
    "Bad Bunny": r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023',
    "Chappell Roan": r'C:\BEYOND40\Shows\Chappell Roan\Chappell Roan Show'
}

# Polling URL for the control panel state
WORKBENCH_URL = "http://192.168.2.99/software/objects?cacheid=/software/site/apps/digistar/ui/controlpanel/Xaq's%20Workbench.dscp;async=true"

# Tkinter GUI setup for logs
root = Tk()
root.title("Digistar Button Listener")
root.geometry("1000x400")

log_panel = scrolledtext.ScrolledText(root)
log_panel.pack(fill='both', expand=True)
log_panel.insert('end', "Listening for button updates...
")

def log(msg):
    timestamp = datetime.now().strftime("[%H:%M:%S] ")
    log_panel.insert('end', timestamp + msg + "\n")
    log_panel.see('end')

# Send command to BEYOND
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            log(f"[BEYOND RESPONSE] {response}")
    except Exception as e:
        log(f"[ERROR sending to BEYOND] {e}")

def start_playlist():
    send_command("PlayListPlay")

def stop_playlist():
    send_command("PlayListStop")

def load_playlist(name):
    if name in playlists:
        send_command(f'LoadPlaylist "{playlists[name]}"')
    else:
        log(f"[ERROR] Unknown playlist: {name}")

# Async XML polling function
async def poll_workbench():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        while True:
            try:
                response = await context.request.get(WORKBENCH_URL)
                body = await response.text()

                root_elem = ET.fromstring(body)
                for attr in root_elem.findall(".//{http://es.com/digistar/2012/03}DsAttributeValue"):
                    obj = attr.find("{http://es.com/digistar/2012/03}Object")
                    val = attr.find("{http://es.com/digistar/2012/03}Value")
                    if obj is not None and val is not None and val.text == "true":
                        button = obj.text.strip()
                        log(f"🎯 Button '{button}' is ON")

                        if button == "Taygete":
                            log("🎵 Triggering: Load Taylor Swift")
                            load_playlist("Taylor Swift")
                        elif button == "asteroidBacchus":
                            log("🎵 Triggering: Load Bad Bunny")
                            load_playlist("Bad Bunny")
                        elif button == "Chaldene":
                            log("🎵 Triggering: Load Chappell Roan")
                            load_playlist("Chappell Roan")
                        elif button == "Hegemone":
                            log("🎵 Triggering: Play current playlist")
                            start_playlist()
                        elif button == "Telesto":
                            log("🎵 Triggering: Stop playlist")
                            stop_playlist()

            except Exception as e:
                log(f"[Polling Error] {e}")
            await asyncio.sleep(1.5)

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(poll_workbench())

ttk.Button(root, text="Start Listener", command=lambda: asyncio.create_task(poll_workbench())).pack(pady=5)
log("Click 'Start Listener' to begin polling.")
root.mainloop()
