"""
Hana Desktop Pet (ハナ・花)
A tiny AI companion girl who lives on your desktop.
- Wanders around the bottom of your screen
- Click her to chat (powered by Google Gemini free tier)

Setup:
  1. pip install requests
  2. Get a free API key: https://aistudio.google.com/apikey
  3. Create a file named "config.txt" next to this script,
     and paste ONLY your API key inside it.
     (Add config.txt to .gitignore if you ever push this repo!)
  4. python hana_pet.py

Note: transparency uses '-transparentcolor', which works on Windows.
"""

import tkinter as tk
import random
import threading
import json
import os
import time

try:
    import requests
except ImportError:
    raise SystemExit("Please run: pip install requests")

# ---------------- CONFIG ----------------
PET_NAME = "Hana"        # change her name here
PET_NAME_JP = "ハナ"      # and here

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")

def load_api_key():
    # priority: environment variable > config.txt
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

API_KEY = load_api_key()
# Free-tier models, tried in order. If the first is overloaded (503)
# or rate-limited (429), Hana automatically falls back to the next.
MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

SYSTEM_PROMPT = (
    f"You are {PET_NAME} ({PET_NAME_JP}), a small friendly girl desktop pet "
    "living on Rudhra's computer. You are cheerful, a little playful, and "
    "helpful — like a kind friend. You love Japanese culture and sometimes "
    "sprinkle in simple Japanese words with their meaning (JLPT N5 level, "
    "to help her learn). Keep replies SHORT: 1-3 sentences max, since you "
    "live in a tiny chat bubble. Never use markdown formatting."
)

PET_SIZE = 100          # canvas size in px
SPEED = 2               # walk speed px/frame
FRAME_MS = 50           # animation tick (ms)
TRANSPARENT = "#010101" # transparency key color

# Hana's colors
BODY = "#ffa8c5"        # soft pink
BODY_DARK = "#e57ba0"   # outline / feet
BLUSH = "#ffd1e0"
FACE = "#4a2c3a"
FLOWER = "#ff5c8a"
FLOWER_CENTER = "#ffe066"
PANEL_BG = "#fff0f5"
HEADER_BG = "#ff8fb3"


class HanaPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)            # no title bar
        self.root.wm_attributes("-topmost", True)   # always on top
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass  # non-Windows fallback: solid background

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        self.x = random.randint(100, self.screen_w - 200)
        self.ground_y = self.screen_h - PET_SIZE - 45  # just above taskbar
        self.y = self.ground_y
        self.vy = 0.0  # vertical velocity for jumping
        self.root.geometry(f"{PET_SIZE}x{PET_SIZE}+{self.x}+{self.y}")

        self.canvas = tk.Canvas(
            self.root, width=PET_SIZE, height=PET_SIZE,
            bg=TRANSPARENT, highlightthickness=0
        )
        self.canvas.pack()

        # state machine
        self.state = "idle"          # idle | walk
        self.direction = 1           # 1 = right, -1 = left
        self.state_timer = 0
        self.tick = 0

        self.chat_window = None
        self.chat_history = []       # [(role, text), ...]

        # drag & throw tracking
        self.dragging = False
        self.vx = 0.0
        self.press_root = (0, 0)
        self.grab_offset = (0, 0)
        self.move_trace = []

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", lambda e: self.root.destroy())  # right-click = quit

        self.animate()

    # ---------------- DRAWING ----------------
    def draw_pet(self):
        c = self.canvas
        c.delete("all")
        t = self.tick
        bounce = 3 if (self.state == "walk" and t % 10 < 5) else 0
        if self.state == "jump":
            bounce = 5  # stretched-up happy pose mid-air
        bx, by = PET_SIZE // 2, PET_SIZE // 2 + 8 - bounce

        # body
        c.create_oval(bx - 30, by - 25, bx + 30, by + 30,
                      fill=BODY, outline=BODY_DARK, width=2)
        # ears
        c.create_polygon(bx - 25, by - 20, bx - 32, by - 45, bx - 8, by - 28,
                         fill=BODY, outline=BODY_DARK, width=2)
        c.create_polygon(bx + 25, by - 20, bx + 32, by - 45, bx + 8, by - 28,
                         fill=BODY, outline=BODY_DARK, width=2)

        # flower on her head (petals + center), sways while walking
        fx = bx + (2 if (self.state == "walk" and t % 20 < 10) else 0)
        fy = by - 38
        for dx, dy in [(-6, 0), (6, 0), (0, -6), (0, 6)]:
            c.create_oval(fx + dx - 4, fy + dy - 4, fx + dx + 4, fy + dy + 4,
                          fill=FLOWER, outline="")
        c.create_oval(fx - 4, fy - 4, fx + 4, fy + 4,
                      fill=FLOWER_CENTER, outline="")

        # eyes (blink every ~4s) with little lashes
        if t % 80 < 74:
            c.create_oval(bx - 15, by - 8, bx - 7, by + 2, fill=FACE, outline="")
            c.create_oval(bx + 7, by - 8, bx + 15, by + 2, fill=FACE, outline="")
            c.create_line(bx - 16, by - 9, bx - 19, by - 12, fill=FACE, width=2)
            c.create_line(bx + 16, by - 9, bx + 19, by - 12, fill=FACE, width=2)
        else:
            c.create_line(bx - 15, by - 3, bx - 7, by - 3, fill=FACE, width=2)
            c.create_line(bx + 7, by - 3, bx + 15, by - 3, fill=FACE, width=2)

        # blush + smile
        c.create_oval(bx - 24, by + 2, bx - 14, by + 9, fill=BLUSH, outline="")
        c.create_oval(bx + 14, by + 2, bx + 24, by + 9, fill=BLUSH, outline="")
        if self.state in ("jump", "thrown"):
            c.create_oval(bx - 5, by + 6, bx + 5, by + 16,
                          fill=FACE, outline="")  # open mouth "wheee!"
        elif self.state == "held":
            c.create_oval(bx - 4, by + 7, bx + 4, by + 15,
                          fill="", outline=FACE, width=2)  # surprised "o"
        else:
            c.create_arc(bx - 8, by + 4, bx + 8, by + 16, start=200, extent=140,
                         style=tk.ARC, outline=FACE, width=2)

        # feet
        foot_shift = 4 if (self.state == "walk" and t % 10 < 5) else 0
        c.create_oval(bx - 22 + foot_shift, by + 24, bx - 6 + foot_shift, by + 34,
                      fill=BODY_DARK, outline="")
        c.create_oval(bx + 6 - foot_shift, by + 24, bx + 22 - foot_shift, by + 34,
                      fill=BODY_DARK, outline="")

    # ---------------- DRAG & THROW ----------------
    def on_press(self, event):
        self.dragging = False
        self.press_root = (event.x_root, event.y_root)
        self.grab_offset = (event.x, event.y)
        self.move_trace = []

    def on_drag(self, event):
        dx = event.x_root - self.press_root[0]
        dy = event.y_root - self.press_root[1]
        if not self.dragging and (abs(dx) > 6 or abs(dy) > 6):
            self.dragging = True
            self.state = "held"
            self.close_chat()
        if self.dragging:
            self.x = event.x_root - self.grab_offset[0]
            self.y = event.y_root - self.grab_offset[1]
            self.move_trace.append((event.x_root, event.y_root))
            if len(self.move_trace) > 5:
                self.move_trace.pop(0)
            self.root.geometry(f"+{self.x}+{self.y}")

    def on_release(self, event):
        if not self.dragging:
            self.toggle_chat()   # it was just a click
            return
        self.dragging = False
        if len(self.move_trace) >= 2:
            (x0, y0), (x1, y1) = self.move_trace[0], self.move_trace[-1]
            n = max(len(self.move_trace) - 1, 1)
            self.vx = (x1 - x0) / n * 1.5   # fling strength
            self.vy = (y1 - y0) / n * 1.5
        else:
            self.vx, self.vy = 0.0, 2.0     # just dropped, fall straight down
        self.state = "thrown"

    # ---------------- BEHAVIOR ----------------
    def animate(self):
        self.tick += 1
        self.state_timer -= 1

        if self.state_timer <= 0 and self.state not in ("jump", "held", "thrown"):
            self.state = random.choice(
                ["idle", "idle", "walk", "walk", "walk", "jump"])
            self.state_timer = random.randint(40, 120)
            if self.state == "walk":
                self.direction = random.choice([-1, 1])
            elif self.state == "jump":
                self.vy = -11.0  # launch upward!

        if self.chat_window is None and not self.dragging:
            if self.state == "walk":
                self.x += SPEED * self.direction
            elif self.state == "jump":
                # small hop forward while airborne
                self.x += (SPEED // 2 + 1) * self.direction
                self.y += int(self.vy)
                self.vy += 1.2  # gravity
                if self.y >= self.ground_y:  # landed
                    self.y = self.ground_y
                    self.vy = 0.0
                    self.state = "idle"
                    self.state_timer = random.randint(20, 60)
            elif self.state == "thrown":
                self.x += int(self.vx)
                self.y += int(self.vy)
                self.vy += 1.2  # gravity
                # bounce off walls and ceiling
                if self.x < 0:
                    self.x, self.vx = 0, -self.vx * 0.7
                elif self.x > self.screen_w - PET_SIZE:
                    self.x, self.vx = self.screen_w - PET_SIZE, -self.vx * 0.7
                if self.y < 0:
                    self.y, self.vy = 0, -self.vy * 0.5
                # bounce on the floor, losing energy each time
                if self.y >= self.ground_y:
                    self.y = self.ground_y
                    if abs(self.vy) > 4:
                        self.vy = -self.vy * 0.5
                        self.vx *= 0.7
                    else:
                        self.vx, self.vy = 0.0, 0.0
                        self.state = "idle"
                        self.state_timer = random.randint(20, 60)

            if self.x < 0:
                self.x, self.direction = 0, 1
            elif self.x > self.screen_w - PET_SIZE:
                self.x, self.direction = self.screen_w - PET_SIZE, -1
            if self.state in ("walk", "jump", "thrown"):
                self.root.geometry(f"+{self.x}+{self.y}")

        self.draw_pet()
        self.root.after(FRAME_MS, self.animate)

    # ---------------- CHAT ----------------
    def toggle_chat(self, event=None):
        if self.chat_window is not None:
            self.close_chat()
            return

        w, h = 320, 260
        cx = min(max(self.x - w // 2 + PET_SIZE // 2, 10), self.screen_w - w - 10)
        cy = max(self.y - h - 45, 10)  # leave room for the title bar

        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title(f"{PET_NAME_JP} {PET_NAME} 🌸")
        self.chat_window.wm_attributes("-topmost", True)
        self.chat_window.geometry(f"{w}x{h}+{cx}+{cy}")
        self.chat_window.configure(bg=PANEL_BG)
        self.chat_window.resizable(False, False)
        self.chat_window.protocol("WM_DELETE_WINDOW", self.close_chat)

        tk.Label(self.chat_window, text=f"{PET_NAME_JP} {PET_NAME} 🌸", bg=HEADER_BG,
                 fg="white", font=("Segoe UI", 10, "bold")).pack(fill="x")

        # IMPORTANT: pack the input bar FIRST (side=bottom) so the
        # expanding chat display can never squeeze it out of the window
        entry_frame = tk.Frame(self.chat_window, bg=PANEL_BG)
        entry_frame.pack(side="bottom", fill="x", padx=6, pady=(0, 6))
        self.entry = tk.Entry(entry_frame, font=("Segoe UI", 11),
                              relief="solid", bd=1)
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", self.send_message)
        tk.Button(entry_frame, text="➤", command=self.send_message,
                  bg=HEADER_BG, fg="white", relief="flat").pack(side="right", padx=(4, 0))

        self.chat_text = tk.Text(self.chat_window, wrap="word", state="disabled",
                                 bg=PANEL_BG, fg=FACE,
                                 font=("Segoe UI", 9), relief="flat")
        self.chat_text.pack(fill="both", expand=True, padx=6, pady=4)

        # focus insurance: any click anywhere on the chat window,
        # or the window gaining focus, drops the cursor into the entry
        self.chat_window.bind("<Button-1>", lambda e: self.entry.focus_set())
        self.chat_window.bind("<FocusIn>", lambda e: self.entry.focus_set())

        if not API_KEY:
            self.append_chat(PET_NAME, "I have no API key yet! Put your free "
                                       "Gemini key in config.txt next to my script. がんばって!")
        else:
            self.append_chat(PET_NAME, "こんにちは Rudhra! What's up? 🌸")
        # Windows sometimes blocks focus for newly opened windows,
        # so retry a few times
        for delay in (50, 200, 500):
            self.chat_window.after(delay, lambda: (
                self.chat_window.lift(),
                self.chat_window.focus_force(),
                self.entry.focus_set()))

    def close_chat(self):
        if self.chat_window:
            self.chat_window.destroy()
            self.chat_window = None

    def append_chat(self, who, text):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", f"{who}: {text}\n\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def send_message(self, event=None):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, "end")
        self.append_chat("You", msg)
        self.chat_history.append(("user", msg))
        self.append_chat(PET_NAME, "…thinking…")
        threading.Thread(target=self.ask_gemini, args=(msg,), daemon=True).start()

    def ask_gemini(self, msg):
        contents = [{"role": "user" if r == "user" else "model",
                     "parts": [{"text": t}]} for r, t in self.chat_history[-10:]]
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
        }
        reply = self._call_gemini(payload)
        self.chat_history.append(("model", reply))
        self.root.after(0, lambda: self.replace_thinking(reply))

    def _call_gemini(self, payload):
        """Try each model in MODELS, retrying on busy (503) / rate limit (429)."""
        last_err = "unknown error"
        for model in MODELS:
            for attempt in range(2):
                try:
                    resp = requests.post(
                        GEMINI_URL.format(model=model, key=API_KEY),
                        headers={"Content-Type": "application/json"},
                        data=json.dumps(payload), timeout=30)
                    data = resp.json()
                    if "error" not in data:
                        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    err = data["error"]
                    code = err.get("code", "?")
                    last_err = f"API error {code}: {err.get('message', err)}"
                    if code in (429, 503):
                        time.sleep(1.5)   # busy — wait, retry, then next model
                        continue
                    return f"({last_err})"   # real error, no point retrying
                except Exception as e:
                    last_err = str(e)
                    time.sleep(1.0)
        return ("(Google's servers are packed right now, gomen! "
                "ちょっとまってね — try me again in a minute 🌸)")

    def replace_thinking(self, reply):
        if not self.chat_window:
            return
        self.chat_text.configure(state="normal")
        # remove the "…thinking…" line
        content = self.chat_text.get("1.0", "end")
        idx = content.rfind(f"{PET_NAME}: …thinking…")
        if idx != -1:
            self.chat_text.delete(f"1.0+{idx}c", "end")
        self.chat_text.configure(state="disabled")
        self.append_chat(PET_NAME, reply)


if __name__ == "__main__":
    HanaPet().root.mainloop()