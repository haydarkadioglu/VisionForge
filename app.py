from __future__ import annotations

import threading
import time

import webview

from backend.api import app


def start_backend() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_backend, daemon=True)
    server_thread.start()

    for _ in range(50):
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:5000/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.1)

    window = webview.create_window(
        "VisionForge",
        "http://127.0.0.1:5000",
        width=1500,
        height=1000,
        resizable=True,
    )
    webview.start(debug=False)
