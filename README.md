# Saeco GranBaristo BLE Controller

Interactive command-line tool to control a Saeco coffee machine (Avanti
BLE protocol, tested on a **Saeco GranBaristo**) over Bluetooth Low
Energy, using the [pysaeco](https://pypi.org/project/pysaeco/) library.

Wake the machine up, read its status, brew a coffee, stop brewing, put it
in standby, or show the pairing PIN on its display, all from a simple
numbered menu.

```
  1  Wake up
  2  Read status
  3  Espresso 45 ml
  4  Coffee 110 ml
  5  American coffee 170 ml
  6  Cappuccino 70/70 ml
  7  Stop brewing
  8  Standby (power off)
  9  Show PIN on machine display
  0  Exit
```

## Requirements

- **A Saeco machine using the Avanti BLE protocol** (confirmed working on
  a GranBaristo; other Avanti-based models may work as well).
- **Bluetooth Low Energy support** on your computer. Developed and tested
  on **Linux (Ubuntu) with BlueZ**. `bleak`, the BLE library pysaeco is
  built on, also supports macOS and Windows, but that hasn't been tested
  with this script.
- **Python 3.9 or newer** (tested with 3.12).
- **The machine's BLE PIN**, found on the machine's own display under the
  Bluetooth/pairing menu. It's a plain decimal number: if the display
  shows something like `0389`, the value to use is `389` (the leading
  zero is just display padding, not a hex or octal marker).

## Installation

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install pysaeco (pulls in bleak, pydantic, anyio, paho-mqtt)
pip install pysaeco
```

## Important: do not pair the machine at the OS level

**Do not pair/bond the coffee machine through your system's Bluetooth
settings (GUI or `bluetoothctl pair`).** The Avanti protocol does not
require BLE-level pairing; authentication happens with the PIN inside
the GATT packets, after a plain connection.

On Linux, an OS-level bond can actually break the connection. On one test
setup (Ubuntu, MacBook with a Broadcom Bluetooth adapter), a bonded
device consistently failed to connect with a
`le-connection-abort-by-local` error until the bond was removed:

```bash
bluetoothctl remove <MAC_ADDRESS>
```

If your machine shows up as connected/paired in your system's Bluetooth
settings, remove it there before running this script.

## Configuration

Open `test3.py` and set your machine's PIN near the top of the file:

```python
PIN = 389   # decimal, as an int. "0389" on the display means 389
```

You don't need to hardcode the MAC address: the script scans for a
device whose name starts with `SAECO` and connects to the first one it
finds. If you have more than one Saeco machine nearby, edit the
`trova_macchina()` function to filter by MAC address instead.

## Usage

```bash
source venv/bin/activate
python3 test3.py
```

The script scans, connects (retrying automatically up to 6 times, since
some Bluetooth adapters occasionally need a few attempts), authenticates
with the PIN, then shows the menu. It stays connected between commands,
so you can run several operations in the same session without
reconnecting each time.

**Put a cup under the spout before choosing a brew option.**

## Coffee recipes

The four available recipes and the volumes used by the menu (edit the
`RICETTE` dictionary in the script to change them):

| Recipe | Coffee | Milk |
|---|---|---|
| Espresso | 45 ml | — |
| Coffee | 110 ml | — |
| American Coffee | 170 ml | — |
| Cappuccino | 70 ml | 70 ml |

pysaeco's recipe classes also support adjusting `aroma`, `prebrew`, and
`temperature` if you want finer control.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `TimeoutError` / repeated `le-connection-abort-by-local` in debug logs | The machine is bonded/paired at the OS level | `bluetoothctl remove <MAC_ADDRESS>`, then retry |
| `AvantiPinError` right after connecting | Wrong PIN | Double check it's the decimal value, no leading-zero confusion; use menu option 9 to display it on the machine |
| `AvantiPinError` on a brew/stop/standby command after status worked once | The PIN session was reset by a previous error (pysaeco clears it on any `AvantiPinError`) | The script re-authenticates automatically on this error; if it still fails, verify the PIN |
| `AvantiNoResponseError` | The machine is off/asleep | Run option 1 (wake up) first, wait a few seconds, then retry |
| No device found during scan | Machine not in range, asleep, or Bluetooth off on your computer | Move closer, wake the machine physically, check your adapter is powered (`bluetoothctl show`) |

For low-level debugging, set `logging.basicConfig(level=logging.DEBUG)`
in the script to see the raw BLE traffic (`bleak` logs every GATT
read/write).

## Credits

Built on top of [pysaeco](https://pypi.org/project/pysaeco/) (MIT
licensed), which implements the Avanti BLE protocol and can also run as
an MQTT bridge for Home Assistant.

## License

MIT. See the pysaeco project for the underlying protocol implementation.
