"""JARVIS chatbox - FREE, runs locally with Ollama. Run: python jarvis_free.py
Setup: 1) install Ollama from ollama.com
       2) in terminal: ollama pull llama3.2
       3) pip install openai
Optional: pip install pyttsx3 (voice)
"""
import os, threading, tkinter as tk
from tkinter import scrolledtext
from openai import OpenAI
import datetime
import json
import re

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SYSTEM = ("You are Riley, a smart, loyal and slightly witty AI assistant. "
          "The user's name is Sabik. Always address the user as 'Supreme Boss', "
          "never as just 'boss' or 'sir'. Be concise and helpful.")
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MEMORY_FILE = "riley_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        return [{"role": "system", "content": SYSTEM}] + saved
    except Exception:
        return [{"role": "system", "content": SYSTEM}]

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[1:][-60:], f, ensure_ascii=False, indent=2)

history = load_memory()

try:
    import pyttsx3
    engine = pyttsx3.init()
except Exception:
    engine = None

BG, FG, ACC = "#050b14", "#00e5ff", "#ff9d00"

def add(tag, text):
    chat.config(state="normal")
    chat.insert(tk.END, text + "\n\n", tag)
    chat.config(state="disabled"); chat.see(tk.END)

def speak(text):
    try:
        import pyttsx3
        eng = pyttsx3.init()
        eng.setProperty("rate", 175)
        eng.setProperty("volume", 1.0)
        eng.say(text)
        eng.runAndWait()
        eng.stop()
    except Exception as e:
        print("Voice error:", e)

import json as _json, urllib.request, urllib.parse

CITY = "Bamberg, Germany"
WMO = {0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
       45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
       61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
       75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "violent showers",
       95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail"}

def _get(url):
    with urllib.request.urlopen(url, timeout=8) as r:
        return _json.loads(r.read().decode())

LAT, LON, PLACE = 49.8917, 10.8892, "Bamberg"

def get_weather():
    try:
        w = _get("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
                 "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
                 "&timezone=auto" % (LAT, LON))["current"]
        desc = WMO.get(w["weather_code"], "unknown conditions")
        return (f"Current weather in {PLACE}: {w['temperature_2m']} C "
                f"(feels like {w['apparent_temperature']} C), {desc}.")
    except Exception as e:
        return f"Weather data is unavailable right now ({e})."

def fix_title(text):
    text = re.sub(r"\b(?<!Supreme )[Bb]oss\b", "Supreme Boss", text)
    text = re.sub(r"\b[Ss]ir\b", "Supreme Boss", text)
    return text

def ask(msg):
    history.append({"role": "user", "content": msg})
    try:
        now = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M")
        sys_msg = {"role": "system",
                                      "content": history[0]["content"] + f" The current local date and time is {now}."
                   + (" " + get_weather() if any(k in msg.lower() for k in ("weather", "temperature", "rain", "forecast", "cold", "hot")) else "")}
        msgs = [sys_msg] + history[1:][-60:]
        r = client.chat.completions.create(model=MODEL, messages=msgs)
        reply = fix_title(r.choices[0].message.content)
        history.append({"role": "assistant", "content": reply})
        save_memory()
    except Exception as e:
        reply = f"Apologies, Supreme Boss. Is Ollama running and the model pulled? Error: {e}"
    root.after(0, lambda: (add("jarvis", "Riley: " + reply), status.config(text="At your Service")))
    speak(reply)

def send(event=None):
    msg = entry.get().strip()
    if not msg: return
    entry.delete(0, tk.END)
    if msg.lower() in ("exit", "quit"):
        root.destroy(); return
    add("user", "YOU: " + msg)
    status.config(text="Thinking...")
    threading.Thread(target=ask, args=(msg,), daemon=True).start()

root = tk.Tk()
root.title("Riley"); root.geometry("500x580"); root.configure(bg=BG)
tk.Label(root, text="R I L E Y", font=("Consolas", 20, "bold"), bg=BG, fg=FG).pack(pady=(8, 0))
status = tk.Label(root, text="Always At your Service", font=("Consolas", 9), bg=BG, fg=ACC); status.pack()
chat = scrolledtext.ScrolledText(root, bg="#0a1624", fg=FG, font=("Consolas", 11),
                                 state="disabled", wrap="word", bd=0)
chat.pack(fill="both", expand=True, padx=10, pady=6)
chat.tag_config("jarvis", foreground=FG); chat.tag_config("user", foreground=ACC)
entry = tk.Entry(root, bg="#0a1624", fg="white", insertbackground=FG, font=("Consolas", 12), bd=0)
entry.pack(fill="x", padx=10, pady=10, ipady=8)
entry.bind("<Return>", send); entry.focus()
add("jarvis", "Riley: Ready to serve you, Supreme Boss.")
root.mainloop()
