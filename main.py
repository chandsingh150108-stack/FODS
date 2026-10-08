"""3D Bin Packing Studio for Factory and Warehouse Logistics.

Entrypoint that launches the modern WebGL Studio application in the default web browser.
"""

from __future__ import annotations

import os
import threading
import webbrowser

from app import app


def main() -> None:
    """Launch the 3D Bin Packing Studio web server and browser interface."""
    port = int(os.environ.get("PORT", 5000))
    url = f"http://localhost:{port}"

    print("\n" + "=" * 60)
    print(" 3D Bin Packing Studio (Warehouse & Logistics)")
    print(f" Web Interface: {url}")
    print("=" * 60 + "\n")

    # Automatically open default browser after a brief moment
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    # Run the production-ready Flask server
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
