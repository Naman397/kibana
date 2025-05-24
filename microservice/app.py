from flask import Flask, request, jsonify
import json
import os
from svm_extractor import detect_timestamps
from threading import Thread
import requests
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

LOG_DIR = "/app/logs"
RAW_LOG_FILE = f"{LOG_DIR}/raw_logs.txt"
OUT_FILE = f"{LOG_DIR}/parsed_logs.json"

@app.route("/parse", methods=["POST"])
def parse_logs():
    parsed = []
    try:
        with open(RAW_LOG_FILE, "r", errors="ignore") as f:
            lines = f.readlines()
            detected = detect_timestamps(lines)
            for line in lines:
                ts = None
                for token in detected['token']:
                    if token in line:
                        ts = token
                        break
                parsed.append({"timestamp": ts, "message": line.strip()})

        with open(OUT_FILE, "w") as out:
            for entry in parsed:
                out.write(json.dumps(entry) + "\n")

        return jsonify({"status": "parsed", "entries": len(parsed)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Watchdog file system handler
class LogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("raw_logs.txt"):
            print("Detected change in logs, triggering parse.")
            try:
                requests.post("http://localhost:5000/parse")
            except Exception as e:
                print("Failed to trigger parse:", e)

# Background file watcher

def watch_logs():
    path = LOG_DIR
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print("Watching logs for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Start file watcher in background
    Thread(target=watch_logs).start()
    # Start Flask app
    app.run(host="0.0.0.0", port=5000)
