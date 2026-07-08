# API Reference

All endpoints return JSON unless noted. CORS headers are set on all responses (`Access-Control-Allow-Origin: *`).

## Status & Info

### `GET /api/status`

Current server and display state.

```json
{
  "ok": true,
  "display_connected": true,
  "queue_running": true,
  "queue_position": 2,
  "messages_count": 5,
  "override_active": false,
  "override_message": {},
  "time_synced": true,
  "settings": { ... },
  "dht22_temp": "23.5",
  "dht22_hum": "45",
  "dht22_ok": true
}
```

### `GET /api/messages`

Full message queue. Returns `{ "messages": [...] }`.

### `GET /api/settings`

Current settings object.

### `GET /api/override`

Current override state. Returns `{ "active": bool, "message": {...}, "expires_at": number }`.

---

## Messages

### `POST /api/messages`

Create a new message. If no `id` is provided, a random 8-char UUID is generated.

**Body:** message object (see Message Fields below)

**Response:** `201 Created` — the created message object with its `id`.

### `PUT /api/messages?id=<id>`

Update an existing message. The body replaces the message entirely (preserving `id`).

**Query:** `id` (required)

**Response:** the updated message object.

### `DELETE /api/messages?id=<id>`

Delete a message.

**Query:** `id` (required)

**Response:** `{ "ok": true }`

### `POST /api/messages/reorder`

Reorder the message queue.

**Body:** `{ "ids": ["id1", "id2", ...] }`

**Response:** `{ "ok": true }`

### `POST /api/skip-to-message?id=<id>`

Jump to a specific message immediately. Cancels any active override, advances the queue, and sends the message to the display.

**Query:** `id` (required)

**Response:** `{ "ok": true, "index": 3 }`

---

## Override

### `POST /api/override`

Set or update the override message. The override replaces the queue while active.

**Body:**
```json
{
  "active": true,
  "message": { "preset_id": "clock", ... },
  "expires_at": 1719000000
}
```

**Response:** the updated override object.

### `POST /api/cancel-override`

Cancel the active override and resume the queue.

**Response:** `{ "ok": true }`

---

## Display

### `POST /api/clear`

Clear both lines of the display.

**Response:** `{ "ok": true }`

### `POST /api/test`

Send a hardcoded test string to the display (body is ignored).

**Response:** `{ "result": "TX: ..." }`

### `POST /api/discover`

Display discovery (stub — only works on ESP firmware).

**Response:** `{ "result": "Discovery only works on ESP (scans addresses 1-31)" }`

---

## Time

### `POST /api/time`

Sync the display's internal clock.

**Body:** `{ "unix_seconds": 1719000000 }`

**Response:** `{ "ok": true }`

---

## Settings

### `PUT /api/settings`

Update settings. Only provided fields are merged in.

**Body:** (any subset)
```json
{
  "display_number": 29,
  "preset_gap_ms": 100,
  "keepalive_sec": 60,
  "queue_running": true,
  "random_mode": false
}
```

**Response:** the full updated settings object.

---

## Message Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | *(auto)* | 8-char unique ID |
| `preset_id` | string | `single-static` | One of the preset names |
| `text` | string | `""` | Main text content |
| `font` | int | `1` | Font size (1-5, depends on preset) |
| `line` | int | `0` | Display line (0=top, 1=bottom) |
| `alignment` | int | `0` | 0=left, 1=center, 2=right |
| `pos_x` | int | `0` | Horizontal start position (px) |
| `width` | int | `96` | Display width (px) |
| `scroll` | int | `0` | Scroll count (0=static, 99=long scroll) |
| `duration_sec` | int | `10` | Seconds to display before next message |
| `persistent` | bool | `true` | Survive server restart |
| `schedule` | object | `{}` | `{ enabled, from_ts, to_ts }` |
| `hidden` | bool | `false` | Skip in normal queue rotation |

### Preset-specific fields

| Preset | Field | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `two-static` | `_ts_font2` | int | `1` | Bottom line font |
| | `_ts_align2` | int | `0` | Bottom line alignment |
| `bus` | `name` | string | `""` | Route number |
| | `_scroll` | string | `""` | Scrolling route info |
| | `_bus_shift` | int | `0` | Manual X-offset for destination |
| `train` | `name` | string | `""` | Train number |
| | `_train_to` | string | `""` | Destination station |
| | `_train_font_from` | int | `1` | Departure font |
| | `_train_font_to` | int | `1` | Destination font |
| | `_train_align_from` | int | `0` | Departure alignment |
| | `_train_align_to` | int | `2` | Destination alignment |
| | `_train_shift` | int | `0` | Manual X-offset for number |
| `clock` | `_clock_shift` | int | `0` | Manual X-offset for time |
| `top-bottom-scroll` | `_tbs_bottom` | string | `""` | Bottom scrolling line |
| | `_tbs_font_top` | int | `1` | Top line font |
| | `_tbs_font_bottom` | int | `1` | Bottom line font |
| | `_tbs_scroll` | int | `99` | Bottom scroll count |
| `imieniny` | `_imieniny_scroll` | int | `99` | Names scroll count |

---

## Web UI

`GET /` or any unmatched path serves `webui.html` — the single-page web interface.
