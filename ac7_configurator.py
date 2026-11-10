"""
ACE COMBAT 7 HOTAS Configurator
Complete GUI for joystick/throttle/rudder configuration

GitHub: https://github.com/YOUR_USERNAME/ac7-hotas-configurator
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import re
import sys

# Check for required dependencies
def check_dependencies():
    """Check and report missing dependencies"""
    missing = []

    try:
        import pygame
    except ImportError:
        missing.append("pygame")

    if missing:
        msg = f"Missing required packages: {', '.join(missing)}\n\n"
        msg += "Install them with:\n"
        msg += f"pip install {' '.join(missing)}"

        # Try to show GUI error if tkinter works
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", msg)
            root.destroy()
        except:
            print(msg)
        sys.exit(1)

check_dependencies()

import pygame

# Windows registry for device detection
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# =============================================================================
# Constants and Device Database
# =============================================================================

VERSION = "1.0.0"

# Known flight sim hardware vendors
KNOWN_VENDORS = {
    0x231D: "VKB",
    0x4098: "WinWing",
    0x044F: "Thrustmaster",
    0x06A3: "Saitek/Logitech",
    0x0738: "Mad Catz",
    0x046D: "Logitech",
    0x1532: "Razer",
    0x045E: "Microsoft",
    0x054C: "Sony",
    0x28DE: "Valve",
    0x1234: "vJoy",
}

# Known device profiles with default bindings
DEVICE_PROFILES = {
    # VKB Gunfighter MCG Ultimate
    (0x231D, 0x0125): {
        'name': 'VKB Gunfighter MCG Ultimate',
        'type': 'stick',
        'bindings': {
            'Flight_Pitch': 'Y:R',
            'Flight_Roll': 'X',
            'Flight_Gun': 'Button1',
            'Flight_Missile': 'Button2',
            'Flight_Weapon': 'Button3',
            'Flight_Target': 'Button4',
            'Flight_Radar': 'Button5',
            'Flight_Flare': 'Button6',
            'Flight_View': 'Button7',
            'Flight_AutoPilot': 'Button8',
            'Flight_HatSwitchUp': 'POV_U1',
            'Flight_HatSwitchDown': 'POV_D1',
            'Flight_HatSwitchLeft': 'POV_L1',
            'Flight_HatSwitchRight': 'POV_R1',
        }
    },
    # VKB Gladiator NXT
    (0x231D, 0x0200): {
        'name': 'VKB Gladiator NXT',
        'type': 'stick',
        'bindings': {
            'Flight_Pitch': 'Y:R',
            'Flight_Roll': 'X',
            'Flight_Yaw': 'Rz',
            'Flight_Gun': 'Button1',
            'Flight_Missile': 'Button2',
            'Flight_Weapon': 'Button3',
            'Flight_Target': 'Button4',
            'Flight_HatSwitchUp': 'POV_U1',
            'Flight_HatSwitchDown': 'POV_D1',
            'Flight_HatSwitchLeft': 'POV_L1',
            'Flight_HatSwitchRight': 'POV_R1',
        }
    },
    # VKB S-TECS Throttle
    (0x231D, 0x012D): {
        'name': 'VKB S-TECS Throttle',
        'type': 'throttle',
        'bindings': {
            'Flight_Throttle': 'Y:R',
            'Flight_CameraPitch': 'Ry',
            'Flight_CameraYaw': 'Rx',
            'Flight_AccelerationDeceleration': 'Button7 + Button8:R',
        }
    },
    # Thrustmaster T.16000M
    (0x044F, 0xB10A): {
        'name': 'Thrustmaster T.16000M',
        'type': 'stick',
        'bindings': {
            'Flight_Pitch': 'Y:R',
            'Flight_Roll': 'X',
            'Flight_Yaw': 'Rz',
            'Flight_Gun': 'Button1',
            'Flight_Missile': 'Button2',
            'Flight_Throttle': 'Slider1:C',
        }
    },
    # Thrustmaster TWCS Throttle
    (0x044F, 0xB687): {
        'name': 'Thrustmaster TWCS Throttle',
        'type': 'throttle',
        'bindings': {
            'Flight_Throttle': 'Z:R:C',
            'Flight_Yaw': 'X',
        }
    },
    # Thrustmaster Warthog Stick
    (0x044F, 0x0402): {
        'name': 'Thrustmaster Warthog Stick',
        'type': 'stick',
        'bindings': {
            'Flight_Pitch': 'Y:R',
            'Flight_Roll': 'X',
            'Flight_Gun': 'Button1',
            'Flight_Missile': 'Button2',
            'Flight_Weapon': 'Button6',
        }
    },
    # Thrustmaster Warthog Throttle
    (0x044F, 0x0404): {
        'name': 'Thrustmaster Warthog Throttle',
        'type': 'throttle',
        'bindings': {
            'Flight_Throttle': 'Z:R:C',
        }
    },
    # Logitech Extreme 3D Pro
    (0x046D, 0xC215): {
        'name': 'Logitech Extreme 3D Pro',
        'type': 'stick',
        'bindings': {
            'Flight_Pitch': 'Y:R',
            'Flight_Roll': 'X',
            'Flight_Yaw': 'Rz',
            'Flight_Throttle': 'Slider1:C',
            'Flight_Gun': 'Button1',
            'Flight_Missile': 'Button2',
        }
    },
}

# AC7 flight functions
FLIGHT_FUNCTIONS = [
    ("Flight_Pitch", "Pitch (Up/Down)"),
    ("Flight_Roll", "Roll (Left/Right)"),
    ("Flight_Yaw", "Yaw (Rudder)"),
    ("Flight_Throttle", "Throttle"),
    ("Flight_Gun", "Gun"),
    ("Flight_Missile", "Missile"),
    ("Flight_Weapon", "Special Weapon"),
    ("Flight_Target", "Target"),
    ("Flight_Radar", "Radar"),
    ("Flight_Flare", "Flare"),
    ("Flight_View", "View Change"),
    ("Flight_AutoPilot", "Autopilot"),
    ("Flight_AccelerationDeceleration", "Accel/Decel"),
    ("Flight_Pause", "Pause"),
    ("Flight_HatSwitchUp", "Hat Up"),
    ("Flight_HatSwitchDown", "Hat Down"),
    ("Flight_HatSwitchLeft", "Hat Left"),
    ("Flight_HatSwitchRight", "Hat Right"),
    ("Flight_CameraPitch", "Camera Pitch"),
    ("Flight_CameraYaw", "Camera Yaw"),
]

AXIS_NAMES = ["X", "Y", "Z", "Rx", "Ry", "Rz", "Slider1", "Slider2"]


# =============================================================================
# Utility Functions
# =============================================================================

def find_ac7_config():
    """Auto-detect AC7 Input.ini location"""
    possible_paths = [
        os.path.expanduser(r"~\AppData\Local\BANDAI NAMCO Entertainment\ACE COMBAT 7\Config\Input.ini"),
        os.path.expandvars(r"%LOCALAPPDATA%\BANDAI NAMCO Entertainment\ACE COMBAT 7\Config\Input.ini"),
        # Steam common locations
        r"C:\Program Files (x86)\Steam\steamapps\common\ACE COMBAT 7\Config\Input.ini",
        r"D:\SteamLibrary\steamapps\common\ACE COMBAT 7\Config\Input.ini",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def get_registry_devices():
    """Scan Windows registry for joystick devices"""
    devices = []
    if not HAS_WINREG:
        return devices

    try:
        key_path = r"System\CurrentControlSet\Control\MediaProperties\PrivateProperties\Joystick\OEM"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    match = re.match(r'VID_([0-9A-Fa-f]+)&PID_([0-9A-Fa-f]+)', subkey_name)
                    if match:
                        vid = int(match.group(1), 16)
                        pid = int(match.group(2), 16)

                        try:
                            with winreg.OpenKey(key, subkey_name) as dev_key:
                                name, _ = winreg.QueryValueEx(dev_key, "OEMName")
                        except:
                            name = "Unknown Device"

                        devices.append({
                            'name': name,
                            'vid': vid,
                            'pid': pid,
                        })
                    i += 1
                except OSError:
                    break
    except Exception as e:
        print(f"Registry scan error: {e}")

    return devices


def get_ac7_section_id(vid, pid):
    """Generate AC7 joystick section ID from VID/PID"""
    if vid and pid:
        return f"Joystick-{pid:04X}{vid:04X}-0000-0000-0000-504944564944"
    return None


def match_device_to_registry(pygame_name, registry_devices):
    """Match a pygame device name to registry entry to get VID/PID"""
    pygame_lower = pygame_name.strip().lower()

    for dev in registry_devices:
        reg_lower = dev['name'].strip().lower()
        # Check for substring match in either direction
        if pygame_lower in reg_lower or reg_lower in pygame_lower:
            return dev['vid'], dev['pid']
        # Check for partial word match
        pygame_words = set(pygame_lower.split())
        reg_words = set(reg_lower.split())
        if len(pygame_words & reg_words) >= 2:
            return dev['vid'], dev['pid']

    return None, None


# =============================================================================
# Device Monitor
# =============================================================================

class DeviceMonitor:
    """Handles pygame joystick detection and monitoring"""

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = []
        self.device_info = []  # Stores VID/PID info
        self.registry_devices = get_registry_devices()

    def refresh(self):
        """Refresh joystick list"""
        pygame.joystick.quit()
        pygame.joystick.init()

        self.joysticks = []
        self.device_info = []

        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()
            self.joysticks.append(js)

            # Get VID/PID
            vid, pid = match_device_to_registry(js.get_name(), self.registry_devices)
            profile = DEVICE_PROFILES.get((vid, pid)) if vid else None

            self.device_info.append({
                'name': js.get_name(),
                'vid': vid,
                'pid': pid,
                'profile': profile,
                'section_id': get_ac7_section_id(vid, pid) if vid else None,
                'num_axes': js.get_numaxes(),
                'num_buttons': js.get_numbuttons(),
                'num_hats': js.get_numhats(),
            })

        return self.joysticks

    def get_state(self, index):
        """Get current state of a joystick"""
        if index < 0 or index >= len(self.joysticks):
            return None

        js = self.joysticks[index]
        pygame.event.pump()

        return {
            'axes': [js.get_axis(i) for i in range(js.get_numaxes())],
            'buttons': [js.get_button(i) for i in range(js.get_numbuttons())],
            'hats': [js.get_hat(i) for i in range(js.get_numhats())],
        }

    def close(self):
        pygame.joystick.quit()
        pygame.quit()


# =============================================================================
# Main Application
# =============================================================================

class AC7Configurator:
    def __init__(self, root):
        self.root = root
        self.root.title(f"ACE COMBAT 7 HOTAS Configurator v{VERSION}")
        self.root.geometry("1150x850")
        self.root.minsize(1000, 700)

        # Core components
        self.monitor = DeviceMonitor()
        self.running = True

        # State
        self.config_path = None
        self.assignments = {}  # func -> {device_index, section_id, input, modifiers}
        self.detected_devices = []

        # Auto-detect config
        self.config_path = find_ac7_config()

        # Build UI
        self.setup_ui()

        # Initial device scan
        self.refresh_devices()

        # Auto-populate if devices found
        self.auto_populate_bindings()

        # Start monitor thread
        self.start_monitor_thread()

    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Input.ini...", command=self.browse_config)
        file_menu.add_command(label="Save", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # Config path indicator
        path_frame = ttk.Frame(self.root)
        path_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(path_frame, text="Config:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text="Not found - Click 'Browse' to locate", foreground="red")
        self.path_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="Browse", command=self.browse_config, width=8).pack(side=tk.RIGHT)

        if self.config_path:
            self.path_label.config(text=self.config_path, foreground="green")

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Detected Devices & Quick Setup
        self.setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_tab, text="Setup")

        # Tab 2: Controller Monitor
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text="Controller Monitor")

        self.setup_setup_tab()
        self.setup_monitor_tab()

    def setup_setup_tab(self):
        """Setup tab with detected devices and quick configuration"""
        main_frame = ttk.Frame(self.setup_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Detected devices section
        devices_frame = ttk.LabelFrame(main_frame, text="Detected Flight Controllers", padding=10)
        devices_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Device list
        columns = ("Device", "Type", "VID:PID", "Status", "Profile")
        self.device_tree = ttk.Treeview(devices_frame, columns=columns, show="headings", height=8)

        self.device_tree.heading("Device", text="Device Name")
        self.device_tree.heading("Type", text="Type")
        self.device_tree.heading("VID:PID", text="VID:PID")
        self.device_tree.heading("Status", text="AC7 Status")
        self.device_tree.heading("Profile", text="Profile")

        self.device_tree.column("Device", width=280)
        self.device_tree.column("Type", width=80)
        self.device_tree.column("VID:PID", width=100)
        self.device_tree.column("Status", width=120)
        self.device_tree.column("Profile", width=150)

        scrollbar = ttk.Scrollbar(devices_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=scrollbar.set)

        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_frame = ttk.Frame(devices_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Refresh Devices", command=self.refresh_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Apply All Profiles", command=self.apply_all_profiles).pack(side=tk.LEFT, padx=5)

        # Current bindings section
        bindings_frame = ttk.LabelFrame(main_frame, text="Current Bindings (from Input.ini)", padding=10)
        bindings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns2 = ("Function", "Device", "Input", "Modifiers")
        self.bindings_tree = ttk.Treeview(bindings_frame, columns=columns2, show="headings", height=10)

        for col in columns2:
            self.bindings_tree.heading(col, text=col)

        self.bindings_tree.column("Function", width=180)
        self.bindings_tree.column("Device", width=200)
        self.bindings_tree.column("Input", width=120)
        self.bindings_tree.column("Modifiers", width=80)

        scrollbar2 = ttk.Scrollbar(bindings_frame, orient=tk.VERTICAL, command=self.bindings_tree.yview)
        self.bindings_tree.configure(yscrollcommand=scrollbar2.set)

        self.bindings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

        self.bindings_tree.bind("<Double-1>", self.on_binding_double_click)

        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="Load from Input.ini", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Save to Input.ini", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Clear All Bindings", command=self.clear_bindings).pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def setup_monitor_tab(self):
        """Live controller monitor for manual binding"""
        main_frame = ttk.Frame(self.monitor_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Device selector
        device_frame = ttk.LabelFrame(main_frame, text="Select Device", padding=10)
        device_frame.pack(fill=tk.X, pady=(0, 10))

        self.device_combo = ttk.Combobox(device_frame, state="readonly", width=60)
        self.device_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)

        self.device_info_label = ttk.Label(device_frame, text="")
        self.device_info_label.pack(side=tk.LEFT, padx=20)

        # Split view
        split_frame = ttk.Frame(main_frame)
        split_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Live input
        input_frame = ttk.LabelFrame(split_frame, text="Live Input", padding=10)
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Axes
        axes_frame = ttk.LabelFrame(input_frame, text="Axes (click Assign to bind)", padding=5)
        axes_frame.pack(fill=tk.X, pady=(0, 10))

        self.axis_bars = []
        self.axis_labels = []

        for i in range(8):
            row = ttk.Frame(axes_frame)
            row.pack(fill=tk.X, pady=2)

            ttk.Label(row, text=f"{AXIS_NAMES[i]}:", width=8).pack(side=tk.LEFT)

            bar = ttk.Progressbar(row, length=150, mode='determinate', maximum=100)
            bar.pack(side=tk.LEFT, padx=5)

            val_label = ttk.Label(row, text="0.00", width=7)
            val_label.pack(side=tk.LEFT)

            btn = ttk.Button(row, text="Assign", width=7,
                           command=lambda idx=i: self.assign_input('axis', idx))
            btn.pack(side=tk.LEFT, padx=5)

            self.axis_bars.append(bar)
            self.axis_labels.append(val_label)

        # Buttons
        buttons_frame = ttk.LabelFrame(input_frame, text="Buttons (click to assign)", padding=5)
        buttons_frame.pack(fill=tk.BOTH, expand=True)

        self.button_canvas = tk.Canvas(buttons_frame, height=150, bg='white')
        self.button_canvas.pack(fill=tk.BOTH, expand=True)
        self.button_canvas.bind("<Button-1>", self.on_button_click)

        # POV Hats
        hats_frame = ttk.LabelFrame(input_frame, text="POV Hats", padding=5)
        hats_frame.pack(fill=tk.X, pady=(10, 0))

        self.hat_labels = []
        for i in range(4):
            lbl = ttk.Label(hats_frame, text=f"POV{i+1}: -")
            lbl.pack(side=tk.LEFT, padx=10)
            self.hat_labels.append(lbl)

        # Right: Assignment panel
        assign_frame = ttk.LabelFrame(split_frame, text="Assign to Function", padding=10)
        assign_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(assign_frame, text="Select function to assign:").pack(anchor=tk.W)

        self.func_listbox = tk.Listbox(assign_frame, height=15)
        self.func_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        for code, name in FLIGHT_FUNCTIONS:
            self.func_listbox.insert(tk.END, f"{code} - {name}")

        # Modifiers
        mod_frame = ttk.LabelFrame(assign_frame, text="Modifiers", padding=5)
        mod_frame.pack(fill=tk.X, pady=5)

        self.reverse_var = tk.BooleanVar()
        self.convert_var = tk.BooleanVar()

        ttk.Checkbutton(mod_frame, text=":R - Reverse/Invert axis", variable=self.reverse_var).pack(anchor=tk.W)
        ttk.Checkbutton(mod_frame, text=":C - Convert range (for throttle)", variable=self.convert_var).pack(anchor=tk.W)

        self.assign_status = ttk.Label(assign_frame, text="Click an axis/button then select function")
        self.assign_status.pack(pady=5)

    # =========================================================================
    # Device Management
    # =========================================================================

    def refresh_devices(self):
        """Refresh and display detected devices"""
        self.monitor.refresh()

        # Clear device tree
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)

        # Update combo boxes
        device_names = []

        for i, info in enumerate(self.monitor.device_info):
            name = info['name']
            vid = info['vid']
            pid = info['pid']
            profile = info['profile']

            # Determine type and status
            vendor = KNOWN_VENDORS.get(vid, "Unknown")
            vid_pid_str = f"{vid:04X}:{pid:04X}" if vid else "Unknown"

            if profile:
                dev_type = profile.get('type', 'unknown').title()
                profile_name = profile.get('name', 'Custom')
                status = "Supported"
            else:
                dev_type = "Unknown"
                profile_name = "None (manual config)"
                status = "Manual Config"

            # Check if it's a known flight sim vendor
            if vid in [0x231D, 0x4098, 0x044F, 0x06A3]:
                tag = "flightsim"
            else:
                tag = "other"

            self.device_tree.insert("", tk.END, values=(
                name[:40], dev_type, vid_pid_str, status, profile_name
            ), tags=(tag,))

            device_names.append(f"{i}: {name[:50]}")

        # Color coding
        self.device_tree.tag_configure("flightsim", background="#e8f5e9")

        # Update combo boxes
        self.device_combo['values'] = device_names
        if device_names:
            self.device_combo.current(0)
            self.on_device_selected(None)

        self.status_label.config(text=f"Found {len(self.monitor.joysticks)} devices")

        # Load config if exists
        if self.config_path:
            self.load_config()

    def on_device_selected(self, event):
        """Handle device selection in monitor tab"""
        idx = self.device_combo.current()
        if idx >= 0 and idx < len(self.monitor.device_info):
            info = self.monitor.device_info[idx]
            self.device_info_label.config(
                text=f"Axes: {info['num_axes']} | Buttons: {info['num_buttons']} | Hats: {info['num_hats']}"
            )

    # =========================================================================
    # Auto-population
    # =========================================================================

    def auto_populate_bindings(self):
        """Auto-populate bindings based on detected devices"""
        for i, info in enumerate(self.monitor.device_info):
            profile = info.get('profile')
            if profile and 'bindings' in profile:
                section_id = info['section_id']
                for func, value in profile['bindings'].items():
                    # Parse value
                    parts = value.split(':')
                    input_str = parts[0]
                    modifiers = ':' + ':'.join(parts[1:]) if len(parts) > 1 else ''

                    self.assignments[func] = {
                        'device_index': i,
                        'device_name': info['name'],
                        'section_id': section_id,
                        'input': input_str,
                        'modifiers': modifiers,
                    }

        self.update_bindings_tree()

    def apply_all_profiles(self):
        """Apply default profiles for all detected devices"""
        applied = 0
        for i, info in enumerate(self.monitor.device_info):
            profile = info.get('profile')
            if profile and 'bindings' in profile:
                section_id = info['section_id']
                for func, value in profile['bindings'].items():
                    parts = value.split(':')
                    input_str = parts[0]
                    modifiers = ':' + ':'.join(parts[1:]) if len(parts) > 1 else ''

                    self.assignments[func] = {
                        'device_index': i,
                        'device_name': info['name'],
                        'section_id': section_id,
                        'input': input_str,
                        'modifiers': modifiers,
                    }
                applied += 1

        self.update_bindings_tree()
        self.status_label.config(text=f"Applied {applied} device profiles")

        if applied > 0:
            if messagebox.askyesno("Save?", f"Applied {applied} profiles.\nSave to Input.ini now?"):
                self.save_config()

    # =========================================================================
    # Monitor Tab Functions
    # =========================================================================

    def start_monitor_thread(self):
        """Start background thread for live input monitoring"""
        def loop():
            while self.running:
                try:
                    self.update_live_monitor()
                except:
                    pass
                time.sleep(0.033)  # ~30Hz

        threading.Thread(target=loop, daemon=True).start()

    def update_live_monitor(self):
        """Update live input display"""
        idx = self.device_combo.current()
        if idx < 0:
            return

        state = self.monitor.get_state(idx)
        if not state:
            return

        # Update axes
        for i, bar in enumerate(self.axis_bars):
            if i < len(state['axes']):
                val = state['axes'][i]
                bar['value'] = (val + 1) * 50
                self.axis_labels[i].config(text=f"{val:+.2f}")
            else:
                bar['value'] = 50
                self.axis_labels[i].config(text="N/A")

        # Update buttons
        self.button_canvas.delete("all")
        cols = 8
        size = 30
        pad = 5

        for i, pressed in enumerate(state['buttons']):
            r, c = i // cols, i % cols
            x, y = c * (size + pad) + pad, r * (size + pad) + pad
            color = "#4CAF50" if pressed else "#E0E0E0"
            self.button_canvas.create_rectangle(x, y, x+size, y+size, fill=color, outline="#333")
            self.button_canvas.create_text(x+size//2, y+size//2, text=str(i+1))

        # Update hats
        dirs = {(0,0): "-", (0,1): "U", (0,-1): "D", (-1,0): "L", (1,0): "R",
                (-1,1): "UL", (1,1): "UR", (-1,-1): "DL", (1,-1): "DR"}
        for i, lbl in enumerate(self.hat_labels):
            if i < len(state['hats']):
                lbl.config(text=f"POV{i+1}: {dirs.get(state['hats'][i], '?')}")

    def on_button_click(self, event):
        """Handle button canvas click"""
        cols, size, pad = 8, 30, 5
        col = (event.x - pad) // (size + pad)
        row = (event.y - pad) // (size + pad)
        btn_idx = row * cols + col

        idx = self.device_combo.current()
        if idx >= 0:
            info = self.monitor.device_info[idx]
            if btn_idx < info['num_buttons']:
                self.assign_input('button', btn_idx)

    def assign_input(self, input_type, input_idx):
        """Assign an input to selected function"""
        selection = self.func_listbox.curselection()
        if not selection:
            self.assign_status.config(text="Select a function first!", foreground="red")
            return

        func_str = self.func_listbox.get(selection[0])
        func_code = func_str.split(" - ")[0]

        device_idx = self.device_combo.current()
        if device_idx < 0:
            return

        info = self.monitor.device_info[device_idx]

        # Build input string
        if input_type == 'axis':
            input_str = AXIS_NAMES[input_idx]
        else:
            input_str = f"Button{input_idx + 1}"

        # Build modifiers
        mods = ""
        if self.reverse_var.get():
            mods += ":R"
        if self.convert_var.get():
            mods += ":C"

        self.assignments[func_code] = {
            'device_index': device_idx,
            'device_name': info['name'],
            'section_id': info['section_id'],
            'input': input_str,
            'modifiers': mods,
        }

        self.update_bindings_tree()
        self.assign_status.config(text=f"Assigned {input_str}{mods} to {func_code}", foreground="green")

    # =========================================================================
    # Config Management
    # =========================================================================

    def browse_config(self):
        """Browse for Input.ini"""
        path = filedialog.askopenfilename(
            title="Select AC7 Input.ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~\\AppData\\Local\\BANDAI NAMCO Entertainment")
        )
        if path:
            self.config_path = path
            self.path_label.config(text=path, foreground="green")
            self.load_config()

    def load_config(self):
        """Load bindings from Input.ini"""
        if not self.config_path or not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r') as f:
                content = f.read()

            self.assignments.clear()
            current_section = None
            current_name = None

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[Joystick-'):
                    current_section = line[1:-1]
                elif line.startswith('ProductName='):
                    current_name = line.split('=', 1)[1].strip().strip('"')
                elif line.startswith('Flight_') and '=' in line and current_section:
                    parts = line.split('=', 1)
                    func, value = parts[0], parts[1].strip()
                    if value:
                        # Parse modifiers
                        if ':' in value:
                            p = value.split(':')
                            input_str = p[0]
                            mods = ':' + ':'.join(p[1:])
                        else:
                            input_str = value
                            mods = ""

                        self.assignments[func] = {
                            'device_name': current_name or "Unknown",
                            'section_id': current_section,
                            'input': input_str,
                            'modifiers': mods,
                        }

            self.update_bindings_tree()
            self.status_label.config(text=f"Loaded {len(self.assignments)} bindings")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        """Save bindings to Input.ini"""
        if not self.config_path:
            messagebox.showerror("Error", "No config file selected.\nUse File > Open Input.ini")
            return

        if not os.path.exists(self.config_path):
            messagebox.showerror("Error", f"Config file not found:\n{self.config_path}")
            return

        try:
            with open(self.config_path, 'r') as f:
                lines = f.readlines()

            # Group assignments by section
            sections = {}
            for func, data in self.assignments.items():
                sec = data.get('section_id')
                if sec:
                    if sec not in sections:
                        sections[sec] = {}
                    sections[sec][func] = data['input'] + data['modifiers']

            # Rewrite file
            new_lines = []
            current_section = None

            for line in lines:
                stripped = line.strip()

                if stripped.startswith('['):
                    current_section = stripped[1:-1] if stripped.endswith(']') else None

                if current_section and current_section.startswith('Joystick-'):
                    if stripped.startswith('Flight_') and '=' in stripped:
                        func = stripped.split('=')[0]
                        if current_section in sections and func in sections[current_section]:
                            new_lines.append(f"{func}={sections[current_section][func]}\n")
                            continue

                new_lines.append(line)

            with open(self.config_path, 'w') as f:
                f.writelines(new_lines)

            self.status_label.config(text="Saved!")
            messagebox.showinfo("Success", f"Saved to:\n{self.config_path}\n\nRestart AC7 to apply changes.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def update_bindings_tree(self):
        """Update the bindings treeview"""
        for item in self.bindings_tree.get_children():
            self.bindings_tree.delete(item)

        for func, data in sorted(self.assignments.items()):
            self.bindings_tree.insert("", tk.END, values=(
                func,
                data.get('device_name', 'Unknown')[:30],
                data['input'],
                data['modifiers']
            ))

    def on_binding_double_click(self, event):
        """Delete binding on double-click"""
        sel = self.bindings_tree.selection()
        if sel:
            item = self.bindings_tree.item(sel[0])
            func = item['values'][0]
            if func in self.assignments:
                if messagebox.askyesno("Delete?", f"Remove binding for {func}?"):
                    del self.assignments[func]
                    self.update_bindings_tree()

    def clear_bindings(self):
        """Clear all bindings"""
        if messagebox.askyesno("Confirm", "Clear all bindings?"):
            self.assignments.clear()
            self.update_bindings_tree()

    # =========================================================================
    # Misc
    # =========================================================================

    def show_about(self):
        """Show about dialog"""
        msg = f"""ACE COMBAT 7 HOTAS Configurator v{VERSION}

A tool for configuring joysticks, throttles, and rudder pedals for ACE COMBAT 7.

Features:
- Auto-detects flight sim hardware
- Pre-configured profiles for popular devices
- Live input monitoring

GitHub: https://github.com/YOUR_USERNAME/ac7-hotas-configurator
"""
        messagebox.showinfo("About", msg)

    def on_closing(self):
        """Clean shutdown"""
        self.running = False
        self.monitor.close()
        self.root.destroy()


# =============================================================================
# Entry Point
# =============================================================================

def main():
    root = tk.Tk()
    app = AC7Configurator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
