# ACE COMBAT 7 HOTAS Configurator

A GUI tool for configuring joysticks, throttles, and rudder pedals for **ACE COMBAT 7: Skies Unknown** on PC.

## Features

- **Auto-detection** of flight sim hardware (VKB, WinWing, Thrustmaster, Saitek, Logitech)
- **Pre-configured profiles** for popular devices
- **Live input monitoring** - see your axes and buttons in real-time
- **Easy binding assignment** - click an input and assign it to a flight function
- Automatic detection of AC7's `Input.ini` location

## Supported Devices

The tool includes built-in profiles for:

| Device | Type | Status |
|--------|------|--------|
| VKB Gunfighter MCG Ultimate | Stick | Full Support |
| VKB Gladiator NXT | Stick | Full Support |
| VKB S-TECS Throttle | Throttle | Full Support |
| Thrustmaster T.16000M | Stick | Full Support |
| Thrustmaster TWCS Throttle | Throttle | Full Support |
| Thrustmaster Warthog | Stick + Throttle | Full Support |
| Logitech Extreme 3D Pro | Stick | Full Support |

**Don't see your device?** You can still use the Controller Monitor tab to manually assign bindings for any DirectInput device.

## Installation

### Prerequisites

- Windows 10/11
- Python 3.8 or higher
- ACE COMBAT 7: Skies Unknown (Steam version)

### Setup

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ac7-hotas-configurator.git
   cd ac7-hotas-configurator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the configurator:**
   ```bash
   python ac7_configurator.py
   ```

   Or double-click `ac7_configurator.py` if Python is associated with `.py` files.

## Usage

### Quick Start

1. Launch the configurator
2. Your connected controllers will be auto-detected in the **Controller Monitor** device selector
3. Choose **Devices > Apply All Profiles** to apply default bindings for detected devices
4. Click **"Save to Input.ini"** to save changes
5. Restart ACE COMBAT 7

### Manual Binding

1. Use the **Controller Monitor** screen
2. Select your device from the dropdown
3. Move an axis or press a button - you'll see it highlighted in the live display
4. Click **"Assign"** next to an axis, or click directly on a button
5. Select the flight function from the list
6. Check modifiers if needed:
   - `:R` - Reverse/invert the axis
   - `:C` - Convert range (required for throttle axes)
7. Save to Input.ini

## AC7 Input.ini Format

For those who want to edit `Input.ini` manually, the format is:

```ini
[Joystick-PPPPVVVV-0000-0000-0000-504944564944]
ProductName="Device Name"
Flight_Pitch=Y:R
Flight_Roll=X
Flight_Throttle=Z:C
Flight_Gun=Button1
```

Where:
- `PPPP` = Product ID (hex, little-endian)
- `VVVV` = Vendor ID (hex, little-endian)

### Axis Modifiers

| Modifier | Description |
|----------|-------------|
| `:R` | Reverse/invert the axis direction |
| `:C` | Convert range from -1.0~1.0 to 0.0~1.0 (use for throttle) |
| `:P` | Positive values only |
| `:N` | Negative values only |

### Available Axes

`X`, `Y`, `Z`, `Rx`, `Ry`, `Rz`, `Slider1`, `Slider2`

### POV Hat Directions

`POV_U1` (up), `POV_D1` (down), `POV_L1` (left), `POV_R1` (right)

Multiple POV hats: `POV_U2`, `POV_D2`, etc.

## Troubleshooting

### Device not detected by the tool

- Make sure the device is connected and powered on
- Try unplugging and reconnecting
- Choose **Devices > Refresh Devices**

### Device identification

The selected device shows its SDL GUID, VID/PID, and identification status.
VID/PID values are read from supported SDL GUID layouts, never guessed from device names.
An identified device can be configured manually even if it has no built-in profile.

If the status is **Identification required**, select the device and click **Set VID/PID**.
Enter the hexadecimal IDs from Windows Device Manager, for example `231D:0200`.
Manual overrides last until device refresh or application restart.
Saving is blocked before writing if any assignment has a missing or invalid joystick section ID;
the error lists the affected functions and devices.

### Device detected by tool but not by AC7

Some devices aren't enumerated by AC7's DirectInput implementation. Options:
1. Use vJoy to create a virtual joystick that AC7 can see
2. Use x360ce to emulate an Xbox controller

### Throttle doesn't work / is inverted

- Make sure to use the `:C` modifier for throttle axes
- Add `:R` to reverse direction if needed
- Example: `Flight_Throttle=Y:R:C`

### Changes not applied in game

- Make sure to save (File > Save or "Save to Input.ini" button)
- **Restart AC7** - the game only reads Input.ini on startup

## Contributing

Contributions are welcome! If you have a device that works with AC7 but isn't in the profiles list, please submit a PR with:

1. Device VID/PID (shown in the tool)
2. Recommended axis/button mappings
3. Any special notes

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

- Inspired by various AC7 HOTAS configuration guides on Steam and Reddit
- Built with Python and pygame

## Disclaimer

This tool modifies ACE COMBAT 7's Input.ini configuration file. While it creates standard-format entries, use at your own risk. Back up your Input.ini before making changes.

Not affiliated with Bandai Namco Entertainment or Project Aces.
