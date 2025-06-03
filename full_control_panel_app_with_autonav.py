
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

# === Send to Beyond ===
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode("utf-8"))
            response = sock.recv(4096).decode("utf-8").strip()
            log_interpreted(f"[BEYOND RESPONSE] {response}")
    except Exception as e:
        log_interpreted(f"[ERROR] {e}")

def start_playlist():
    send_command("PlayListPlay")

def stop_playlist():
    send_command("PlayListStop")

def load_playlist(name):
    if name in playlists:
        send_command(f'LoadPlaylist "{playlists[name]}"')
    else:
        log_interpreted(f"[ERROR] Unknown playlist: {name}")

# === UI Setup ===
root = tk.Tk()
root.title("Digistar Listener + Beyond Trigger App")
root.geometry("1400x800")

# Layout Panels
top_frame = ttk.Frame(root)
top_frame.pack(fill=tk.X, padx=5, pady=5)

url_var = tk.StringVar(value="http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")
ttk.Entry(top_frame, textvariable=url_var, width=100).pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Button(top_frame, text="Go", command=lambda: threading.Thread(target=run).start()).pack(side=tk.LEFT, padx=5)

quick_frame = ttk.Frame(root)
quick_frame.pack(fill=tk.X, padx=5)
ttk.Button(quick_frame, text="Control Panel", command=lambda: open_url("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")).pack(side=tk.LEFT)
ttk.Button(quick_frame, text="YouTube", command=lambda: open_url("https://www.youtube.com/watch?v=LXuSOkf2M3c")).pack(side=tk.LEFT)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

fetch_panel = scrolledtext.ScrolledText(main_frame, width=45)
fetch_panel.pack(side=tk.LEFT, fill=tk.Y)
fetch_panel.insert("end", "Fetch/XHR Feed:\n")
fetch_panel.tag_config("request", foreground="green")
fetch_panel.tag_config("response", foreground="red")

log_panel = scrolledtext.ScrolledText(main_frame)
log_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_panel.insert("end", "Command Log:\n")

interpreted_panel = scrolledtext.ScrolledText(main_frame, width=50, height=8)
interpreted_panel.pack(side=tk.TOP, fill=tk.X)
interpreted_panel.insert("end", "Interpreted Events:\n")

full_item_panel = scrolledtext.ScrolledText(main_frame, width=50, height=8)
full_item_panel.pack(side=tk.BOTTOM, fill=tk.X)
full_item_panel.insert("end", "Full Item:\n")

def log(panel, msg, tag=None):
    timestamp = datetime.now().strftime("[%H:%M:%S] ")
    if tag:
        panel.insert("end", timestamp + msg + "\n", tag)
    else:
        panel.insert("end", timestamp + msg + "\n")
    panel.see("end")

def log_interpreted(msg): log(interpreted_panel, msg)
def log_cmd(msg): log(log_panel, msg)
def insert_fetch(msg, tag): log(fetch_panel, msg, tag)

def open_url(url): url_var.set(url); threading.Thread(target=run).start()

def truncate(msg, limit=120): return msg if len(msg) <= limit else msg[:limit] + "..."

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        log_cmd(f"🌐 Navigating to {url_var.get()}")
        await page.goto(url_var.get())

        # === Auto Navigation ===
        async def try_click(selector, label):
            while True:
                try:
                    await page.click(selector)
                    log_cmd(f"[INFO] Clicked {label}")
                    break
                except:
                    log_cmd(f"[WAIT] {label} not ready...")
                    await asyncio.sleep(1)

        await try_click("#playout", "menu icon")
        await try_click("text=Zach's Group", "group")
        await try_click("text=Xaq's Workbench", "Xaq's Workbench")
        log_cmd("[✅] Navigation complete.")

        # === Polling Workbench
        async def poll():
            while True:
                try:
                    log_cmd("[DEBUG] Polling...")
                    resp = await page.request.get("http://192.168.2.99/software/objects?cacheid=/software/site/apps/digistar/ui/controlpanel/Xaq's%20Workbench.dscp;async=true")
                    body = await resp.text()
                    log_cmd("[DEBUG] Response received.")
                    log_cmd(body)

                    if "<Object>Taygete</Object>" in body and "<Value>true</Value>" in body:
                        log_interpreted("➡️ Taygete ON → Load Taylor Swift")
                        load_playlist("Taylor Swift")
                    elif "<Object>asteroidBacchus</Object>" in body and "<Value>true</Value>" in body:
                        log_interpreted("➡️ Bacchus ON → Load Bad Bunny")
                        load_playlist("Bad Bunny")
                    elif "<Object>Chaldene</Object>" in body and "<Value>true</Value>" in body:
                        log_interpreted("➡️ Chaldene ON → Load Chappell Roan")
                        load_playlist("Chappell Roan")
                    elif "<Object>Hegemone</Object>" in body and "<Value>true</Value>" in body:
                        log_interpreted("➡️ Hegemone ON → Start Playlist")
                        start_playlist()
                    elif "<Object>Telesto</Object>" in body and "<Value>true</Value>" in body:
                        log_interpreted("➡️ Telesto ON → Stop Playlist")
                        stop_playlist()

                except Exception as e:
                    log_cmd(f"[Polling Error] {e}")
                await asyncio.sleep(8)

        await poll()

threading.Thread(target=lambda: asyncio.run(run())).start()
root.mainloop()
