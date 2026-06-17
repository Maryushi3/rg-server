# RG Display Server

Local HTTP server for controlling R&G LED displays over RS485.

## Quick Start

```bash
# Find your USB RS485 dongle
ls /dev/cu.usbmodem*

# Run the server
python server.py --serial /dev/cu.usbmodemXXXX --port 8080
```

Open http://localhost:8080/ in a browser.

## Requirements

- Python 3
- `pyserial` (`pip install pyserial`)

## Usage

```
python server.py [--port 8080] [--serial /dev/cu.usbmodemXXX]
```

- `--port`: HTTP port (default 8080)
- `--serial`: RS485 serial device path. If not specified or unavailable, runs in simulation mode (no display).

## API

See `API.md` in the esp32-display-controller project for the full API spec.

## Files

- `server.py` — HTTP server + RS485 driver
- `webui.html` — Web-based user interface
