import threading
import asyncio
import nest_asyncio
import socket
from datetime import datetime
from playwright.async_api import async_playwright
import tkinter as tk
import requests
import xml.etree.ElementTree as ET
from tkinter import ttk, scrolledtext, StringVar

import os

playlists = {}  # Display name → file path
buttons = {}    # Button name → display name

def load_playlist_config(txt_path="playlists.txt"):
    if not os.path.exists(txt_path):
        print(f"[WARN] Playlist file '{txt_path}' not found.")
        return

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    button, display, path = [x.strip() for x in line.split("=", 2)]
                    playlists[display] = path
                    buttons[button] = display
                except ValueError:
                    print(f"[SKIP] Malformed line in playlist file: {line}")

load_playlist_config()


nest_asyncio.apply()

# === BEYOND Configuration ===
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024.BeyondSL',
    "Bad Bunny":    r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023.BeyondSL',
    "Chappell Roan": r'C:\BEYOND40\Shows\Chappel Roan\Chappel Roan 2025.BeyondSL'
}

full_messages = []

# === BEYOND Command Handling ===
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            interpreted_panel.insert(tk.END, f"[BEYOND RESPONSE] {response}\n")
            interpreted_panel.see(tk.END)
    except Exception as e:
        interpreted_panel.insert(tk.END, f"[ERROR] {e}\n")
        interpreted_panel.see(tk.END)

def start_playlist(): send_command("PlayListPlay")
def stop_playlist(): send_command("PlayListStop")
def load_playlist(name):
    path = playlists.get(name)
    if path:
        send_command(f'LoadPlaylist "{path}"')
    else:
        interpreted_panel.insert(tk.END, f"[ERROR] Unknown playlist: {name}\n")
        interpreted_panel.see(tk.END)

# === UI Setup ===
root = tk.Tk()
root.title("Command Listener Browser")
root.geometry("1200x700")

url_var = StringVar()
url_var.set("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")

top_frame = ttk.Frame(root)
top_frame.pack(fill=tk.X, padx=5, pady=5)

address_entry = ttk.Entry(top_frame, textvariable=url_var, width=100)
address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

go_button = ttk.Button(top_frame, text="Go", command=lambda: threading.Thread(target=start_all).start())
go_button.pack(side=tk.LEFT, padx=5)

quick_frame = ttk.Frame(root)
quick_frame.pack(fill=tk.X, padx=5)

def open_xaqs_workbench():
    try:
        url = "http://192.168.2.99/Software/Site/Apps/Digistar/UI/ControlPanel/Xaq's%20Workbench.dscp"
        response = requests.get(url, timeout=5)
        log_panel.insert(tk.END, f"\n🧪 Sent GET to Workbench: {response.status_code} {response.reason}\n")
    except Exception as e:
        log_panel.insert(tk.END, f"\n❌ Error opening workbench: {e}\n")
    log_panel.see(tk.END)

# Quick buttons
ttk.Button(quick_frame, text="Open Xaq's Workbench", command=open_xaqs_workbench).pack(side=tk.LEFT)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Left panels
log_panel = scrolledtext.ScrolledText(main_frame)
log_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_panel.insert(tk.END, "Command Log:\n")

interpreted_panel = scrolledtext.ScrolledText(main_frame, width=140, height=8)
interpreted_panel.pack(side=tk.BOTTOM, fill=tk.X)
interpreted_panel.insert(tk.END, "Interpreted Events:\n")

# Right panels
right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

fetch_panel = scrolledtext.ScrolledText(right_frame, width=40, height=20)
fetch_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
fetch_panel.insert(tk.END, "Fetch/XHR Feed:\n")

full_item_panel = scrolledtext.ScrolledText(right_frame, width=40, height=10)
full_item_panel.pack(side=tk.BOTTOM, fill=tk.BOTH)
full_item_panel.insert(tk.END, "Full Item:\n")

fetch_panel.tag_config("request", foreground="green")
fetch_panel.tag_config("response", foreground="red")
fetch_panel.tag_config("marker", background="lightgray")

def insert_with_tag(panel, msg, tag):
    full_messages.append(msg)
    timestamp = datetime.now().strftime("[%H:%M:%S] ")
    truncated = msg if len(msg) <= 120 else msg[:120] + "..."
    is_at_bottom = panel.yview()[1] >= 0.99
    panel.insert(tk.END, f"{timestamp}{truncated}\n", tag)
    if is_at_bottom:
        panel.see(tk.END)

def on_fetch_click(event):
    index = fetch_panel.index(f"@{event.x},{event.y}")
    line = int(str(index).split(".")[0]) - 2
    if 0 <= line < len(full_messages):
        full_item_panel.delete("1.0", tk.END)
        full_item_panel.insert(tk.END, full_messages[line])

def on_fetch_right_click(event):
    index = fetch_panel.index(f"@{event.x},{event.y}")
    line_num = str(index).split(".")[0]
    fetch_panel.insert(f"{line_num}.0", "────────────── MARK ──────────────\n", "marker")

fetch_panel.bind("<Button-1>", on_fetch_click)
fetch_panel.bind("<Button-3>", on_fetch_right_click)

# === Combined Browser: Auto-Nav + Listener ===
async def start_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        async def log_request(request):
            method, url = request.method, request.url
            message = f"🟢 {method} REQUEST: {url}"
            try:
                if method == "POST":
                    body = await request.post_data()
                    if body:
                        message += f"\n📦 POST BODY: {body}"
            except Exception as e:
                message += f"\n⚠️ Error reading body: {e}"
            insert_with_tag(fetch_panel, message, "request")

        async def log_response(response):
            url = response.url
            message = f"🔴 RESPONSE: {url}"
            try:
                content = await response.text()
                full_messages.append(content)
                timestamp = datetime.now().strftime("[%H:%M:%S] ")
                try:
                    root = ET.fromstring(content)
                    for attr in root.findall(".//{http://es.com/digistar/2012/03}DsAttributeValue"):
                        object_name = attr.find("{http://es.com/digistar/2012/03}Object")
                        value = attr.find("{http://es.com/digistar/2012/03}Value")
                        if object_name is not None and value is not None and value.text == "true":
                            obj = object_name.text.strip()
                            interpreted_panel.insert(tk.END, f"🎯 Button '{obj}' is ON\n")
                            interpreted_panel.see(tk.END)

                            if obj in buttons:
                                show = buttons[obj]
                                interpreted_panel.insert(tk.END, f"🎵 Triggering: Load {show}\n")
                                load_playlist(show)
                            elif obj == "Hegemone":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Play current playlist\n")
                                start_playlist()
                            elif obj == "Telesto":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Stop playlist\n")
                                stop_playlist()

                except ET.ParseError:
                    pass
            except Exception as e:
                full_messages.append(f"[Error reading body: {e}]")
            is_at_bottom = fetch_panel.yview()[1] >= 0.99
            fetch_panel.insert(tk.END, f"{timestamp}{message}\n", "response")
            if is_at_bottom:
                fetch_panel.see(tk.END)

        page.on("request", log_request)
        page.on("response", log_response)

        log_panel.insert(tk.END, "[INFO] Navigating to control panel menu...\n")
        await page.goto("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")

        async def try_click(selector, label):
            while True:
                try:
                    await page.click(selector, timeout=3000)
                    break
                except:
                    log_panel.insert(tk.END, f"[WAIT] {label} not ready...\n")
                    log_panel.see(tk.END)
                    await asyncio.sleep(1)

        await asyncio.sleep(2)
        await try_click("#Xaq\\'s\\ Mixed\\ Multiverse", "group")
        await asyncio.sleep(1)
        await try_click("#Xaq\\'s\\ Workbench", "Workbench page")
        log_panel.insert(tk.END, "[INFO] Navigation Complete.\n")
        log_panel.see(tk.END)

        while True:
            await asyncio.sleep(1)

def start_all():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_browser())

threading.Thread(target=start_all, daemon=True).start()
root.mainloop()
