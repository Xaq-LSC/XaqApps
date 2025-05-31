import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import time
import socket
from playwright.sync_api import sync_playwright

# ===== BEYOND CONTROL CONFIGURATION =====

# IP/port for Beyond TCP/IP talk server
BEYOND_IP = "192.168.2.19"
BEYOND_PORT = 16063

# Pre‐configured playlists (adjust paths as needed)
playlists = {
    "Taylor Swift": r'C:\BEYOND40\Shows\Taylor Swift Laser\TaylorSwiftPlaylist2024',
    "Bad Bunny":    r'C:\BEYOND40\Shows\Bad Bunny\Bad Bunny Laser Show 2023',
    "Sabrina Carpenter": r'C:\BEYOND40\Shows\Sabrina Carpenter\Sabrina Carpenter'
}

# Send a command string to Beyond and log the response (or error)
def send_command(command):
    try:
        with socket.create_connection((BEYOND_IP, BEYOND_PORT), timeout=5) as sock:
            sock.sendall((command + "\r\n").encode('utf-8'))
            response = sock.recv(4096).decode('utf-8').strip()
            combined_app.log_beyond(f"[BEYOND RESPONSE] {response}")
    except Exception as e:
        combined_app.log_beyond(f"[ERROR] {e}")

# “Start / Stop / Pause” wrappers for Beyond
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
        combined_app.log_beyond(f"[ERROR] Unknown playlist: {name}")

def send_custom_command():
    cmd = combined_app.custom_command_entry.get()
    send_command(cmd)


# ===== NETWORK MONITOR CONFIGURATION =====

# Three preset test URLs (Digistar control panel, a YouTube video, example.com)
DIGISTAR_URL = "http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1"
YOUTUBE_URL  = "https://www.youtube.com/watch?v=LXuSOkf2M3c"
EXAMPLE_URL  = "https://example.com/"

# Keywords to look for in incoming URLs (case‐insensitive)
KEYWORDS = {
    "sender": "Sender",
    "screen": "Screen",
    "module": "Module"
}


class CombinedApp:
    def __init__(self, root):
        self.root = root
        root.title("Beyond Remote Control + Network Monitor")
        root.geometry("1600x900")

        # === BEYOND REMOTE CONTROL FRAME ===
        beyond_frame = tk.LabelFrame(root, text="BEYOND Remote Control", padx=10, pady=10)
        beyond_frame.pack(fill=tk.X, padx=10, pady=5)

        #  → Output log for Beyond responses/errors
        self.output_text = ScrolledText(beyond_frame, height=10)
        self.output_text.pack(fill=tk.X, pady=5)
        self.log_beyond("🟢 BEYOND Remote Control Ready.")

        #  → Buttons to control playlists
        button_frame = tk.Frame(beyond_frame)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="▶️ Start Playlist", command=start_playlist, width=20).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="⏸ Pause Playlist", command=pause_playlist, width=20).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="⏹ Stop Playlist",  command=stop_playlist,  width=20).grid(row=2, column=0, padx=5, pady=5)

        for idx, name in enumerate(playlists.keys()):
            tk.Button(button_frame, text=f"Load {name}", command=lambda n=name: load_playlist(n), width=20)\
                .grid(row=idx, column=1, padx=5, pady=5)

        #  → Custom command entry box
        self.custom_command_entry = tk.Entry(beyond_frame, width=40)
        self.custom_command_entry.pack(pady=5)
        tk.Button(beyond_frame, text="Send Custom Command", command=send_custom_command).pack(pady=5)

        # === NETWORK MONITOR FRAME ===
        monitor_frame = tk.LabelFrame(root, text="Network Monitor (Digistar)", padx=10, pady=10)
        monitor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        #  → Top controls: URL entry, Go button, preset buttons
        top_frame = tk.Frame(monitor_frame)
        top_frame.pack(fill=tk.X, pady=5)

        tk.Label(top_frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = tk.Entry(top_frame, width=80)
        self.url_entry.insert(0, DIGISTAR_URL)
        self.url_entry.pack(side=tk.LEFT, padx=5)

        self.go_button = tk.Button(top_frame, text="Go", command=self.start_monitor)
        self.go_button.pack(side=tk.LEFT, padx=5)

        # Preset buttons to set the URL quickly
        tk.Button(top_frame, text="Control Panel", command=lambda: self.set_url(DIGISTAR_URL)).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="YouTube Test",  command=lambda: self.set_url(YOUTUBE_URL)).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="Example.com",  command=lambda: self.set_url(EXAMPLE_URL)).pack(side=tk.LEFT, padx=2)

        #  → Main monitor area: placeholder for browser + feed panel
        main_pane = tk.PanedWindow(monitor_frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True)

        #    • Placeholder for embedded browser (we open Chromium separately)
        self.browser_placeholder = tk.Label(
            main_pane,
            text="Browser window opened separately\n(embedded not supported)",
            bg="lightgray",
            width=60,
            height=15
        )
        main_pane.add(self.browser_placeholder)

        #    • Right: raw network response feed (truncated)
        right_panel = tk.Frame(main_pane)
        self.feed_area = ScrolledText(right_panel)
        self.feed_area.pack(fill=tk.BOTH, expand=True)
        self.feed_area.insert(tk.END, "📡 Incoming Network Responses (truncated):\n")
        main_pane.add(right_panel, width=700)

        #  → Bottom: interpreted events log
        self.log_area = ScrolledText(monitor_frame, height=8)
        self.log_area.pack(fill=tk.X, padx=5, pady=5)
        self.log_area.insert(tk.END, "🟢 Interpreted Events:\n")


    def log_beyond(self, message):
        """Log messages in the BEYOND output panel."""
        try:
            self.output_text.after(0, lambda: self.output_text.insert(tk.END, message + "\n"))
            self.output_text.after(0, lambda: self.output_text.see(tk.END))
        except:
            print(message)

    def log_feed(self, message):
        """Log raw incoming network responses (truncated)."""
        lines = message.splitlines()
        if len(lines) > 2:
            lines = lines[:2]
            lines.append("... (truncated)")
        snippet = "\n".join(
            line if len(line) <= 200 else line[:200] + "..."
            for line in lines
        )
        self.feed_area.insert(tk.END, snippet + "\n")
        self.feed_area.see(tk.END)

    def log_event(self, message):
        """Log interpreted events under the monitor."""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def set_url(self, url):
        """Set the URL entry to a preset."""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)

    def start_monitor(self):
        """Launch the browser + network monitor in a background thread."""
        threading.Thread(target=self.run_monitor, daemon=True).start()

    def run_monitor(self):
        """Use Playwright + CDP to watch incoming responses."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            client = context.new_cdp_session(page)
            client.send("Network.enable")
            client.send("Network.setCacheDisabled", {"cacheDisabled": True})

            def on_response(event):
                try:
                    url = event["response"]["url"]
                    # Log every incoming response
                    self.log_feed(f"RESPONSE {url}")

                    # Keyword checks in URL → interpreted event
                    for key, label in KEYWORDS.items():
                        if key in url.lower():
                            self.log_event(f"🟡 {label}")

                    # Detect OriStick on within /software/objects polling
                    if "/software/objects" in url:
                        body = client.send("Network.getResponseBody", {"requestId": event["requestId"]})
                        text = body.get("body", "")
                        if "OriStick on" in text or "OriStick%20on" in text:
                            self.log_event("🟢 Orion pressed detected in incoming data")
                            # Example: trigger a Beyond command automatically:
                            # send_command("PlayListPlay")
                except Exception as e:
                    self.log_feed(f"[Error parsing response: {e}]")

            client.on("Network.responseReceived", on_response)

            target = self.url_entry.get()
            page.goto(target)
            self.log_feed(f"🌐 Navigated to {target}")

            # Keep the listener alive until you close the Chromium window
            while not page.is_closed():
                time.sleep(0.5)


# ==== INSTANTIATE & RUN APP ====
if __name__ == "__main__":
    combined_app = None
    root = tk.Tk()
    combined_app = CombinedApp(root)
    root.mainloop()
