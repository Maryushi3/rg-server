#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8080}"

detect_devices_mac() {
  ls /dev/cu.usbmodem* /dev/cu.usbserial* 2>/dev/null || true
}

detect_devices_linux() {
  ls /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA* 2>/dev/null || true
}

detect_devices() {
  case "$(uname -s)" in
    Darwin) detect_devices_mac ;;
    Linux)  detect_devices_linux ;;
    *)      echo "" ;;
  esac
}

SERIAL=""
ARDUINO_SERIAL=""

# Usage
usage() {
  echo "Usage: $0 [--serial /dev/...] [--arduino-serial /dev/...]" >&2
  exit 1
}

# Parse named args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial) SERIAL="$2"; shift 2 ;;
    --arduino-serial) ARDUINO_SERIAL="$2"; shift 2 ;;
    *) usage ;;
  esac
done

# If not specified, auto-detect RS485 interface
if [[ -z "$SERIAL" ]]; then
  DEVICES=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && DEVICES+=("$line")
  done < <(detect_devices)

  if [[ ${#DEVICES[@]} -eq 0 ]]; then
    echo "No RS485 interface detected automatically." >&2
    echo "Starting in SIMULATION MODE (no display)." >&2
    echo "Pass --serial /dev/... to use a specific device." >&2
  elif [[ ${#DEVICES[@]} -eq 1 ]]; then
    echo "Single serial device found: ${DEVICES[0]}" >&2
    echo "Is this the RS485 display interface or the DHT22 Arduino?" >&2
    read -rp "[R]S485 or [A]rduino? " role < /dev/tty
    if [[ "$role" =~ ^[Aa] ]]; then
      ARDUINO_SERIAL="${DEVICES[0]}"
      echo "Arduino: $ARDUINO_SERIAL  (starting in simulation mode for RS485)" >&2
    else
      SERIAL="${DEVICES[0]}"
      echo "RS485: $SERIAL" >&2
    fi
  else
    echo "Multiple USB serial devices detected:" >&2
    DEVICE_DESCS=()
    for i in "${!DEVICES[@]}"; do
      desc=""
      if command -v system_profiler &>/dev/null; then
        desc=$(system_profiler SPUSBDataType 2>/dev/null | grep -B3 "${DEVICES[$i]}" | head -3 | grep -E 'Product:|Manufacturer:' | tr -d ' ' | tr '\n' ' ' || true)
      elif command -v udevadm &>/dev/null; then
        desc=$(udevadm info --name="${DEVICES[$i]}" 2>/dev/null | grep -E 'ID_MODEL=|ID_VENDOR=' | head -2 | cut -d= -f2 | tr '\n' ' ' || true)
      fi
      DEVICE_DESCS[$i]="$desc"
      echo "  [$((i+1))] ${DEVICES[$i]}  $desc" >&2
    done
    echo "" >&2
    echo "Which is the RS485 display interface?" >&2
    read -rp "Choose [1-${#DEVICES[@]}] or 0 for none: " choice < /dev/tty
    choice="${choice:-0}"
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#DEVICES[@]} )); then
      SERIAL="${DEVICES[$((choice-1))]}"
      echo "RS485: $SERIAL" >&2
    fi
    # Remaining devices — ask if one is the Arduino
    if [[ -z "$ARDUINO_SERIAL" ]]; then
      REMAINING=()
      for i in "${!DEVICES[@]}"; do
        [[ "${DEVICES[$i]}" != "$SERIAL" ]] && REMAINING+=("${DEVICES[$i]}")
      done
      if [[ ${#REMAINING[@]} -eq 1 ]]; then
        echo "" >&2
        echo "Detected additional device: ${REMAINING[0]} — is this the DHT22 Arduino?" >&2
        read -rp "Use as Arduino sensor? [Y/n]: " yn < /dev/tty
        if [[ "$yn" =~ ^[Nn] ]]; then
          : # skip
        else
          ARDUINO_SERIAL="${REMAINING[0]}"
          echo "Arduino: $ARDUINO_SERIAL" >&2
        fi
      elif [[ ${#REMAINING[@]} -gt 1 ]]; then
        echo "" >&2
        echo "Which is the DHT22 Arduino?" >&2
        for i in "${!REMAINING[@]}"; do
          echo "  [$((i+1))] ${REMAINING[$i]}  ${DEVICE_DESCS[$((i+1))]}" >&2
        done
        read -rp "Choose [1-${#REMAINING[@]}] or 0 for none: " choice2 < /dev/tty
        choice2="${choice2:-0}"
        if [[ "$choice2" =~ ^[0-9]+$ ]] && (( choice2 >= 1 && choice2 <= ${#REMAINING[@]} )); then
          ARDUINO_SERIAL="${REMAINING[$((choice2-1))]}"
          echo "Arduino: $ARDUINO_SERIAL" >&2
        fi
      fi
    fi
  fi
fi

cd "$SCRIPT_DIR"
ARGS="--port $PORT"
[[ -n "$SERIAL" ]] && ARGS="$ARGS --serial $SERIAL"
[[ -n "$ARDUINO_SERIAL" ]] && ARGS="$ARGS --arduino-serial $ARDUINO_SERIAL"
exec python3 server.py $ARGS
