import threading
import asyncio
import nest_asyncio
import socket
from datetime import datetime
from playwright.async_api import async_playwright
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests  # Add to the top of your file if not already
import xml.etree.ElementTree as ET


nest_asyncio.apply()

# === BEYOND Configuration ===
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024.BeyondSL',
    "Bad Bunny":    r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023.BeyondSL',
    "Chappell Roan": r'C:\BEYOND40\Shows\Chappel Roan\Chappel Roan 2025.BeyondSL'
}

# === Globals ===
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

def start_playlist():
    send_command("PlayListPlay")

def stop_playlist():
    send_command("PlayListStop")

def load_playlist(name):
    if name in playlists:
        send_command(f'LoadPlaylist "{playlists[name]}"')
    else:
        interpreted_panel.insert(tk.END, f"[ERROR] Unknown playlist: {name}\n")
        interpreted_panel.see(tk.END)

# === UI Setup ===
root = tk.Tk()
root.title("Command Listener Browser")
root.geometry("1200x700")

url_var = tk.StringVar()
url_var.set("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")

top_frame = ttk.Frame(root)
top_frame.pack(fill=tk.X, padx=5, pady=5)

address_entry = ttk.Entry(top_frame, textvariable=url_var, width=100)
address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

def start_browser():
    threading.Thread(target=run).start()

go_button = ttk.Button(top_frame, text="Go", command=start_browser)
go_button.pack(side=tk.LEFT, padx=5)

quick_frame = ttk.Frame(root)
quick_frame.pack(fill=tk.X, padx=5)

def set_url_and_go(url):
    url_var.set(url)
    start_browser()

ttk.Button(quick_frame, text="Control Panel", command=lambda: set_url_and_go("http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1")).pack(side=tk.LEFT)
ttk.Button(quick_frame, text="YouTube Test", command=lambda: set_url_and_go("https://www.youtube.com/watch?v=LXuSOkf2M3c")).pack(side=tk.LEFT)
ttk.Button(quick_frame, text="Example Site", command=lambda: set_url_and_go("https://jsonplaceholder.typicode.com/")).pack(side=tk.LEFT)

def open_xaqs_workbench():
    try:
        url = "http://192.168.2.99/Software/Site/Apps/Digistar/UI/ControlPanel/Xaq's%20Workbench.dscp"
        response = requests.get(url, timeout=5)
        log_panel.insert(tk.END, f"🧪 Sent GET to Workbench: {response.status_code} {response.reason}\n")
    except Exception as e:
        log_panel.insert(tk.END, f"❌ Error opening workbench: {e}\n")
    log_panel.see(tk.END)

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

# Right panels (Fetch + Full Item)
right_frame = ttk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

fetch_panel = scrolledtext.ScrolledText(right_frame, width=40, height=20)
fetch_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
fetch_panel.insert(tk.END, "Fetch/XHR Feed:\n")

full_item_panel = scrolledtext.ScrolledText(right_frame, width=40, height=10)
full_item_panel.pack(side=tk.BOTTOM, fill=tk.BOTH)
full_item_panel.insert(tk.END, "Full Item:\n")

# Color tags
fetch_panel.tag_config("request", foreground="green")
fetch_panel.tag_config("response", foreground="red")
fetch_panel.tag_config("marker", background="lightgray")

# Panel update logic
def insert_with_tag(panel, msg, tag):
    full_messages.append(msg)
    index = len(full_messages) - 1
    timestamp = datetime.now().strftime("[%H:%M:%S] ")
    truncated = truncate_msg(msg)
    
    # Auto-scroll logic
    is_at_bottom = panel.yview()[1] >= 0.99
    
    panel.insert(tk.END, f"{timestamp}{truncated}\n", tag)
    if is_at_bottom:
        panel.see(tk.END)

def on_fetch_click(event):
    index = fetch_panel.index(f"@{event.x},{event.y}")
    line = int(str(index).split(".")[0]) - 2  # Adjust for header
    if 0 <= line < len(full_messages):
        full_item_panel.delete("1.0", tk.END)
        full_item_panel.insert(tk.END, full_messages[line])

def on_fetch_right_click(event):
    index = fetch_panel.index(f"@{event.x},{event.y}")
    line_num = str(index).split(".")[0]
    fetch_panel.insert(f"{line_num}.0", "────────────── MARK ──────────────\n", "marker")

fetch_panel.bind("<Button-1>", on_fetch_click)
fetch_panel.bind("<Button-3>", on_fetch_right_click)

def truncate_msg(msg, max_chars=120):
    return msg if len(msg) <= max_chars else msg[:max_chars] + "..."

# === Async Browser + Listener ===
async def browse_and_listen():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        async def log_request(request):
            method = request.method
            url = request.url
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
            is_execute = "execute?command=" in url
            arrow = "➡️ " if is_execute else ""
            message = f"🔴 {arrow}RESPONSE: {url}"

            # Try to read body and extract useful signal
            try:
                content = await response.text()
                full_messages.append(content)  # so clicking shows full body
                timestamp = datetime.now().strftime("[%H:%M:%S] ")

                # Try to detect signal keywords
                lower_content = content.lower()
                if "taygete" in lower_content or "bacchus" in lower_content or "chaldene" in lower_content:
                    message += f"\n🎯 Possible match found in body!"

            except Exception as e:
                content = f"[Error reading body: {e}]"
                full_messages.append(content)

            # Scroll logic
            is_at_bottom = fetch_panel.yview()[1] >= 0.99
            fetch_panel.insert(tk.END, f"{timestamp}{truncate_msg(message)}\n", "response")
            if is_at_bottom:
                fetch_panel.see(tk.END)

        async def log_response(response):
            url = response.url
            is_execute = "execute?command=" in url
            arrow = "➡️ " if is_execute else ""
            message = f"🔴 {arrow}RESPONSE: {url}"

            try:
                content = await response.text()
                full_messages.append(content)  # for full panel view
                timestamp = datetime.now().strftime("[%H:%M:%S] ")

                # Parse XML to look for "true" status on any button
                try:
                    root = ET.fromstring(content)
                    for attr in root.findall(".//{http://es.com/digistar/2012/03}DsAttributeValue"):
                        object_name = attr.find("{http://es.com/digistar/2012/03}Object")
                        value = attr.find("{http://es.com/digistar/2012/03}Value")
                        if object_name is not None and value is not None and value.text == "true":
                            obj = object_name.text.strip()
                            interpreted_panel.insert(tk.END, f"🎯 Button '{obj}' is ON\n")
                            interpreted_panel.see(tk.END)

                            if obj == "Taygete":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Load Taylor Swift\n")
                                load_playlist("Taylor Swift")
                            elif obj == "asteroidBacchus":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Load Bad Bunny\n")
                                load_playlist("Bad Bunny")
                            elif obj == "Chaldene":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Load Chappell Roan\n")
                                load_playlist("Chappell Roan")
                            elif obj == "Hegemone":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Play current playlist\n")
                                start_playlist()
                            elif obj == "Telesto":
                                interpreted_panel.insert(tk.END, "🎵 Triggering: Stop playlist\n")
                                stop_playlist()

                except ET.ParseError:
                    pass  # not XML? no worries

            except Exception as e:
                full_messages.append(f"[Error reading body: {e}]")

            is_at_bottom = fetch_panel.yview()[1] >= 0.99
            fetch_panel.insert(tk.END, f"{timestamp}{truncate_msg(message)}\n", "response")
            if is_at_bottom:
                fetch_panel.see(tk.END)



        page.on("request", log_request)
        page.on("response", log_response)

        url = url_var.get()
        log_panel.insert(tk.END, f"\n🌐 Navigating to {url}\n")
        await page.goto(url)

        while True:
            await asyncio.sleep(1)

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(browse_and_listen())
    except Exception as e:
        log_panel.insert(tk.END, f"❌ Error in run(): {e}\n")
        log_panel.see(tk.END)

root.mainloop()

