import threading
import asyncio
import nest_asyncio
import socket
from playwright.async_api import async_playwright
import tkinter as tk
from tkinter import ttk, scrolledtext

nest_asyncio.apply()

# === BEYOND Configuration ===
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024',
    "Bad Bunny":    r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023',
    "Chappell Roan": r'C:\BEYOND40\Shows\Chappell Roan\Chappell Roan Show'
}

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

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

interpreted_panel = scrolledtext.ScrolledText(main_frame, width=140, height=8)
interpreted_panel.pack(side=tk.BOTTOM, fill=tk.X)
interpreted_panel.insert(tk.END, "Interpreted Events:\n")

fetch_panel = scrolledtext.ScrolledText(main_frame, width=40)
fetch_panel.pack(side=tk.RIGHT, fill=tk.Y)
fetch_panel.insert(tk.END, "Fetch/XHR Feed:\n")

log_panel = scrolledtext.ScrolledText(main_frame)
log_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_panel.insert(tk.END, "Command Log:\n")

async def browse_and_listen():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        async def log_response(response):
            url = response.url
            msg = f"RESPONSE: {url}\n"
            fetch_panel.insert(tk.END, msg)
            fetch_panel.see(tk.END)

            if "execute?command=" in url:
                interpreted_panel.insert(tk.END, f"🎵 Command Detected: {url}\n")
                interpreted_panel.see(tk.END)
                if "Taygete%20on" in url:
                    interpreted_panel.insert(tk.END, "🎵 Beyond Command: Load Taylor Swift\n")
                    interpreted_panel.see(tk.END)
                    load_playlist("Taylor Swift")
                elif "asteroidBacchus%20on" in url:
                    interpreted_panel.insert(tk.END, "🎵 Beyond Command: Load Bad Bunny\n")
                    interpreted_panel.see(tk.END)
                    load_playlist("Bad Bunny")
                elif "Chaldene%20on" in url:
                    interpreted_panel.insert(tk.END, "🎵 Beyond Command: Load Chappell Roan\n")
                    interpreted_panel.see(tk.END)
                    load_playlist("Chappell Roan")
                elif "Hegemone%20on" in url:
                    interpreted_panel.insert(tk.END, "🎵 Beyond Command: Play current playlist\n")
                    interpreted_panel.see(tk.END)
                    start_playlist()
                elif "Telesto%20on" in url:
                    interpreted_panel.insert(tk.END, "🎵 Beyond Command: Stop playlist\n")
                    interpreted_panel.see(tk.END)
                    stop_playlist()

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
