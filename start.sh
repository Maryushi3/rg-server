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

# Precedence: 1) --serial arg  2) auto-detect
if [[ $# -ge 2 && "$1" == "--serial" ]]; then
  SERIAL="$2"
elif [[ $# -ge 1 && "$1" != "--serial" ]]; then
  echo "Usage: $0 [--serial /dev/...]" >&2
  exit 1
elif [[ $# -eq 0 ]]; then
  DEVICES=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && DEVICES+=("$line")
  done < <(detect_devices)

  if [[ ${#DEVICES[@]} -eq 0 ]]; then
    echo "No RS485 interface detected automatically." >&2
    echo "Starting in SIMULATION MODE (no display)." >&2
    echo "Pass --serial /dev/... to use a specific device." >&2
  elif [[ ${#DEVICES[@]} -eq 1 ]]; then
    SERIAL="${DEVICES[0]}"
    echo "Detected RS485 interface: $SERIAL" >&2
  else
    echo "Multiple RS485 interfaces detected:" >&2
    for i in "${!DEVICES[@]}"; do
      desc=""
      if command -v system_profiler &>/dev/null; then
        desc=$(system_profiler SPUSBDataType 2>/dev/null | grep -B3 "${DEVICES[$i]}" | head -3 | grep -E 'Product:|Manufacturer:' | tr -d ' ' | tr '\n' ' ' || true)
      elif command -v udevadm &>/dev/null; then
        desc=$(udevadm info --name="${DEVICES[$i]}" 2>/dev/null | grep -E 'ID_MODEL=|ID_VENDOR=' | head -2 | cut -d= -f2 | tr '\n' ' ' || true)
      fi
      echo "  [$((i+1))] ${DEVICES[$i]}  $desc" >&2
    done
    read -rp "Choose interface [1-${#DEVICES[@]}]: " choice < /dev/tty
    choice="${choice:-1}"
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#DEVICES[@]} )); then
      SERIAL="${DEVICES[$((choice-1))]}"
    else
      echo "Invalid choice, running in SIMULATION MODE." >&2
    fi
  fi
fi

cd "$SCRIPT_DIR"
exec python3 server.py --port "$PORT" ${SERIAL:+--serial "$SERIAL"}
