import tkinter as tk
import pyautogui
import threading
import time
import random
import ctypes

class MouseJigglerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Jiggler")
        self.root.geometry("350x250")
        
        self.jiggling = False
        self.jiggle_interval = 5  # Default interval in seconds

        self.label = tk.Label(root, text="Mouse Jiggler")
        self.label.pack(pady=10)

        self.jiggle_button = tk.Button(root, text="Jiggle Mouse Now", command=self.jiggle_mouse)
        self.jiggle_button.pack(pady=5)

        self.interval_label = tk.Label(root, text="Jiggle Interval (seconds):")
        self.interval_label.pack()

        self.interval_entry = tk.Entry(root)
        self.interval_entry.insert(0, "2")
        self.interval_entry.pack()

        self.toggle_button = tk.Button(root, text="Start Jiggling", command=self.toggle_jiggling)
        self.toggle_button.pack(pady=10)

        self.status_label = tk.Label(root, text="")
        self.status_label.pack()

        self.keys_to_press = ['shift', 'ctrl', 'alt']

    def jiggle_mouse(self):
        try:
            # Bring the app window to front
            self.bring_to_front()

            # Jiggling the mouse in a noticeable circle
            pyautogui.move(50, 0)  
            pyautogui.move(0, 50)
            pyautogui.move(-50, 0)
            pyautogui.move(0, -50)

            # Randomly select a key to press
            key = random.choice(self.keys_to_press)

            # Special handling for Tab (we press it and then unpress immediately)
            if key == 'tab':
                pyautogui.keyDown(key)
                pyautogui.keyUp(key)
            else:
                pyautogui.keyDown(key)
                time.sleep(0.1)  # Hold for 100 milliseconds
                pyautogui.keyUp(key)
            
            # Show which key was pressed
            self.status_label.config(text=f"{key.capitalize()} Pressed!")
            self.root.configure(bg="#018c0f")
            self.root.after(500, self.reset_visual)
        except Exception as e:
            print(f"Error jiggling: {e}")

    def bring_to_front(self):
        try:
            ctypes.windll.user32.SetForegroundWindow(self.root.winfo_id())
        except:
            pass

    def reset_visual(self):
        self.status_label.config(text="")
        self.root.configure(bg="#f0f0f0")

    def toggle_jiggling(self):
        if self.jiggling:
            self.jiggling = False
            self.toggle_button.config(text="Start Jiggling")
        else:
            self.jiggling = True
            self.toggle_button.config(text="Stop Jiggling")
            self.start_jiggling_thread()

    def start_jiggling_thread(self):
        thread = threading.Thread(target=self.jiggler)
        thread.daemon = True
        thread.start()

    def jiggler(self):
        while self.jiggling:
            try:
                self.jiggle_interval = int(self.interval_entry.get())
            except ValueError:
                self.jiggle_interval = 5

            self.jiggle_mouse()
            time.sleep(self.jiggle_interval)

root = tk.Tk()
app = MouseJigglerApp(root)
root.mainloop()
