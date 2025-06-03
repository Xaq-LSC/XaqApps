
import threading
import asyncio
import nest_asyncio
import socket
from playwright.async_api import async_playwright
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

nest_asyncio.apply()

# === BEYOND Configuration ===
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024',
    "Bad Bunny":    r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023',
    "Chappell Roan": r'C:\BEYOND40\Shows\Chappell Roan\Chappell Roan Show'
}

# === UI Setup ===
root = tk.Tk()
root.title("Command Listener Browser")
root.geometry("1300x800")

url_var = tk.StringVar()
url_var.set("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")

top_frame = ttk.Frame(root)
top_frame.pack(fill=tk.X, padx=5, pady=5)

address_entry = ttk.Entry(top_frame, textvariable=url_var, width=100)
address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

quick_frame = ttk.Frame(root)
quick_frame.pack(fill=tk.X, padx=5)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

interpreted_panel = scrolledtext.ScrolledText(main_frame, width=140, height=8)
interpreted_panel.pack(side=tk.BOTTOM, fill=tk.X)
interpreted_panel.insert(tk.END, "Interpreted Events:\n")

fetch_panel = scrolledtext.ScrolledText(main_frame, width=40)
fetch_panel.pack(side=tk.RIGHT, fill=tk.Y)
fetch_panel.insert(tk.END, "Fetch/XHR Feed:\n")

# Setup color tags
fetch_panel.tag_config("request", foreground="green")
fetch_panel.tag_config("response", foreground="red")

log_panel = scrolledtext.ScrolledText(main_frame)
log_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_panel.insert(tk.END, "Command Log:\n")

# === Logging helpers ===
def log(panel, msg):
    timestamp = datetime.now().strftime("[%H:%M:%S] ")
    panel.after(0, lambda: panel.insert("end", timestamp + msg + "\n"))

def log_cmd(msg): log(log_panel, msg)
def log_fetch(msg, tag): fetch_panel.after(0, lambda: insert_with_tag(fetch_panel, msg, tag))

def insert_with_tag(panel, msg, tag):
    panel.insert(tk.END, msg, tag)
    panel.insert(tk.END, "\n")

# === BEYOND Command Sender ===
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            log(interpreted_panel, f"[BEYOND RESPONSE] {response}")
    except Exception as e:
        log(interpreted_panel, f"[ERROR] {e}")

def start_playlist(): send_command("PlayListPlay")
def stop_playlist(): send_command("PlayListStop")
def load_playlist(name):
    if name in playlists:
        send_command(f'LoadPlaylist "{playlists[name]}"')
    else:
        log(interpreted_panel, f"[ERROR] Unknown playlist: {name}")

# === Navigation + Listening ===
async def try_click(page, selector, label):
    try:
        await page.click(selector)
        log_cmd(f"[CLICKED] {label}")
    except Exception as e:
        log_cmd(f"[FAIL] {label}: {e}")

async def auto_navigate(page):
    await try_click(page, "#playout", "menu icon")
    await asyncio.sleep(1)
    await try_click(page, "text=Laser Show Controls", "Laser Show Controls group")
    await asyncio.sleep(1)
    await try_click(page, "text=Xaq's Workbench", "Xaq's Workbench panel")
    await asyncio.sleep(1)
    log_cmd("[DONE] Navigation Complete")

async def browse_and_listen():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        url = url_var.get()
        log_cmd(f"🌐 Navigating to {url}")
        await page.goto(url)
        await auto_navigate(page)

        async def log_request(request):
            msg = request.url
            log_fetch(f"🟢 REQUEST: {msg}", "request")

        async def log_response(response):
            msg = response.url
            log_fetch(f"🔴 RESPONSE: {msg}", "response")
            if "execute?command=" in msg:
                log(interpreted_panel, f"➡️ Command Detected: {msg}")
                if "Taygete%20on" in msg:
                    log(interpreted_panel, "🎵 Beyond Command: Load Taylor Swift")
                    load_playlist("Taylor Swift")
                elif "asteroidBacchus%20on" in msg:
                    log(interpreted_panel, "🎵 Beyond Command: Load Bad Bunny")
                    load_playlist("Bad Bunny")
                elif "Chaldene%20on" in msg:
                    log(interpreted_panel, "🎵 Beyond Command: Load Chappell Roan")
                    load_playlist("Chappell Roan")
                elif "Hegemone%20on" in msg:
                    log(interpreted_panel, "🎵 Beyond Command: Play playlist")
                    start_playlist()
                elif "Telesto%20on" in msg:
                    log(interpreted_panel, "🎵 Beyond Command: Stop playlist")
                    stop_playlist()

        page.on("request", log_request)
        page.on("response", log_response)

        while True:
            await asyncio.sleep(1)

def run_browser():
    asyncio.run(browse_and_listen())

ttk.Button(top_frame, text="Go", command=lambda: threading.Thread(target=run_browser).start()).pack(side=tk.LEFT, padx=5)

root.mainloop()
