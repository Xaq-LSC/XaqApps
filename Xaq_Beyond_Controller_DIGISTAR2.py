from playwright.sync_api import sync_playwright
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import time

# URL to Digistar control panel
DEFAULT_URL = "http://192.168.2.99/software/config/host/web/controlpanel.htm?bk=1"

class NetworkMonitorApp:
    def __init__(self, root):
        self.root = root
        root.title("Digistar Incoming Traffic Monitor")
        root.geometry("1400x800")

        # Top controls
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, pady=5)

        tk.Label(top_frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = tk.Entry(top_frame, width=80)
        self.url_entry.insert(0, DEFAULT_URL)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        self.go_button = tk.Button(top_frame, text="Go", command=self.start_monitor)
        self.go_button.pack(side=tk.LEFT, padx=5)

        # Split main area
        main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left: placeholder for embedded browser
        self.browser_placeholder = tk.Label(
            main_frame, text="Browser window opened separately\n(embedded not supported)", 
            bg="lightgray", width=50, height=10
        )
        main_frame.add(self.browser_placeholder)

        # Right: raw network response log
        right_panel = tk.Frame(main_frame)
        self.feed_area = ScrolledText(right_panel)
        self.feed_area.pack(fill=tk.BOTH, expand=True)
        self.feed_area.insert(tk.END, "📡 Incoming Network Responses (truncated):\n")
        main_frame.add(right_panel, width=600)

        # Bottom: interpreted events
        self.log_area = ScrolledText(root, height=8)
        self.log_area.pack(fill=tk.X, padx=10, pady=5)
        self.log_area.insert(tk.END, "🟢 Interpreted Events:\n")

    def log_event(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def log_feed(self, message):
        # Truncate to two lines or 200 chars
        lines = message.splitlines()
        if len(lines) > 2:
            lines = lines[:2]
            lines.append("... (truncated)")
        snippet = "\n".join(line if len(line) <= 200 else line[:200] + "..." for line in lines)
        self.feed_area.insert(tk.END, snippet + "\n")
        self.feed_area.see(tk.END)

    def start_monitor(self):
        threading.Thread(target=self.run, daemon=True).start()
        self.go_button.config(state=tk.DISABLED)

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Attach CDP session for network events
            client = context.new_cdp_session(page)
            client.send("Network.enable")

            def on_response(event):
                try:
                    url = event["response"]["url"]
                    self.log_feed(f"RESPONSE {url}")
                    if "/software/objects" in url:
                        body = client.send("Network.getResponseBody", {"requestId": event["requestId"]})
                        text = body.get("body", "")
                        if "OriStick on" in text or "OriStick%20on" in text:
                            self.log_event("🟢 Orion pressed detected in incoming data")
                except Exception as e:
                    self.log_feed(f"[Error parsing response: {e}]")

            client.on("Network.responseReceived", on_response)

            target = self.url_entry.get()
            page.goto(target)
            self.log_feed(f"🌐 Navigated to {target}")

            # Keep alive until browser closes
            while not page.is_closed():
                time.sleep(0.5)

# Run app
root = tk.Tk()
app = NetworkMonitorApp(root)
root.mainloop()

