# RG Display Server

HTTP server for controlling R&G LED displays over RS485. Features a web UI for queue management, override, presets, scheduling, namedays, and DHT22 sensor display.

## Quick Start

```bash
# Auto-detect serial devices (interactive)
./start.sh

# Or specify devices directly
./start.sh --serial /dev/cu.usbmodem2101 --arduino-serial /dev/cu.usbmodem2103

# Or run directly (simulation mode if no serial device)
python3 server.py --port 8080
```

Open http://localhost:8080 in a browser.

## Requirements

- Python 3
- `pyserial` (`pip install pyserial`)
- On Raspberry Pi with MAX485: `RPi.GPIO` (`pip install RPi.GPIO`)

## Raspberry Pi Setup

Connect MAX485 to the Pi's UART on GPIO 14 (TXD) and 15 (RXD). Tie RE and DE together to a free GPIO pin (e.g. GPIO 26). Enable the UART in `/boot/config.txt`:

```
enable_uart=1
dtoverlay=disable-bt   # frees ttyAMA0 (PL011 UART) from Bluetooth
```

Reboot, then run:

```bash
pip install pyserial RPi.GPIO
./start.sh --serial /dev/ttyAMA0 --rs485-gpio 26
```

## Usage

```bash
python3 server.py [--port PORT] [--serial DEVICE] [--arduino-serial DEVICE]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | `8080` | HTTP server port |
| `--serial` | `/dev/ttyAMA0` | RS485 display serial device. Runs in simulation mode if not found. |
| `--arduino-serial` | *(none)* | Serial port for DHT22 temperature/humidity sensor |
| `--rs485-gpio` | *(none)* | BCM GPIO pin tied to MAX485 RE+DE for direction control |

## start.sh

The `start.sh` script auto-detects USB serial devices and interactively prompts you to assign each one (RS485 display or DHT22 Arduino). Supports macOS and Linux. Override detection with `--serial` or `--arduino-serial`. Set `PORT` environment variable to change the HTTP port.

## Files

| File | Purpose |
|------|---------|
| `server.py` | HTTP server + RS485 display driver + queue logic |
| `webui.html` | Single-page web interface |
| `start.sh` | Interactive device detection launcher |
| `messages.json` | Persisted message queue (gitignored) |
| `settings.json` | Persisted settings (gitignored) |

## Presets

Each message has a `preset_id` that determines how it renders on the display:

| Preset | Description |
|--------|-------------|
| `single-static` | Single line of static text |
| `scrolling` | Single line of scrolling text |
| `two-static` | Two static lines (separated by `\|\|` in text) |
| `top-bottom-scroll` | Top static line, bottom scrolling line |
| `bus` | Bus route (big font left) + destination (small font right) + scrolling route info |
| `train` | Train station display (from/to + train number) |
| `clock` | Current time (big font) + date + weekday |
| `imieniny` | Polish nameday display (top static, bottom scrolling names) |
| `imieniny-static` | Polish nameday — top "IMIENINY", bottom 2-3 names static |
| `imieniny-scroll` | Single scrolling line "Imieniny: &lt;names&gt;" |
| `do-konca-roku` | Days until end of year — top text, bottom count (checkbox for split rows) |
| `do-konca-roku-scroll` | Single scrolling line with count |
| `dht22` | Temperature and humidity from DHT22 sensor |

## Queue

Messages cycle in order with a configurable duration (`duration_sec`, default 10s). Supports:
- **Random mode**: picks a random visible message instead of sequential
- **Scheduling**: per-message time windows (from/to)
- **Persistence**: saved to `messages.json` on every mutation
- **Hidden messages**: skipped during normal rotation

## Override

A temporary message that replaces the queue. Supports an expiry timestamp. Clock and nameday overrides refresh every ~1 second. The "Save to Messages" button copies the current override into the queue.

## Settings

Settings are saved to `settings.json`:

| Field | Default | Description |
|-------|---------|-------------|
| `display_number` | `29` | RS485 display address |
| `preset_gap_ms` | `100` | Gap between multi-frame presets (min ~50ms) |
| `keepalive_sec` | `60` | Keepalive interval |
| `queue_running` | `true` | Whether the queue loop is active |
| `random_mode` | `false` | Random message selection |

## Credits

This project would not exist without the protocol analysis and notes shared by [Mitsumi](https://github.com/Mitsumi) and [LirekPL](https://github.com/LirekPL) in the [rg-screens-things](https://github.com/HiszpanInk/rg-screens-things) repository — the definitive resource for understanding R&G display communication. Thanks for the dumps, the docs, and the hardware.
