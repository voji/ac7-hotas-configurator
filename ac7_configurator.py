"""
ACE COMBAT 7 HOTAS Configurator
Complete GUI for joystick/throttle/rudder configuration

GitHub: https://github.com/YOUR_USERNAME/ac7-hotas-configurator
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
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


def get_guid_vid_pid(guid):
    """Decode the standard SDL2 GUID layout; never infer IDs from a name.

    Matches SDL 2.28.4 SDL_GetJoystickGUIDInfo's standard-layout checks:
    https://github.com/libsdl-org/SDL/blob/release-2.28.4/src/joystick/SDL_joystick.c
    """
    if not isinstance(guid, str) or not re.fullmatch(r'[0-9a-fA-F]{32}', guid):
        return None, None
    raw = bytes.fromhex(guid)
    bus = int.from_bytes(raw[:2], 'little')
    if not (bus < 0x20 or bus == 0xFF):
        return None, None
    if raw[6:8] != b'\0\0' or raw[10:12] != b'\0\0':
        return None, None
    vid = int.from_bytes(raw[4:6], 'little')
    pid = int.from_bytes(raw[8:10], 'little')
    return (vid, pid) if vid and pid else (None, None)


def get_ac7_section_id(vid, pid):
    """Generate AC7 joystick section ID from VID/PID"""
    if vid and pid:
        return f"Joystick-{pid:04X}{vid:04X}-0000-0000-0000-504944564944"
    return None


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

            guid = js.get_guid()
            vid, pid = get_guid_vid_pid(guid)
            profile = DEVICE_PROFILES.get((vid, pid)) if vid else None

            self.device_info.append({
                'name': js.get_name(),
                'guid': guid,
                'identity_source': 'Automatic' if vid else 'Identification required',
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
        self.monitor_after_id = None
        self.button_items = []
        self.button_states = []

        # State
        self.config_path = None
        self.assignments = {}  # func -> {device_index, section_id, input, modifiers}
        self.detected_devices = []
        self.loaded_bindings = set()
        self.loaded_sections = {}

        # Auto-detect config
        self.config_path = find_ac7_config()

        # Build UI
        self.setup_ui()

        # Initial device scan
        self.refresh_devices()

        # Keep existing configuration; defaults are applied only on request.

        # Schedule monitoring on the Tkinter main thread
        self.schedule_monitor_update()

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

        device_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Devices", menu=device_menu)
        device_menu.add_command(label="Refresh Devices", command=self.refresh_devices)
        device_menu.add_command(label="Apply All Profiles", command=self.apply_all_profiles)

        self.monitor_frame = ttk.Frame(self.root)
        self.monitor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.setup_monitor()

    def setup_monitor(self):
        """Live controller monitor for manual binding"""
        main_frame = ttk.Frame(self.monitor_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        ttk.Button(bottom_frame, text="Load from Input.ini", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Save to Input.ini", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Clear All Bindings", command=self.clear_bindings).pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(bottom_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Device selector
        device_frame = ttk.LabelFrame(main_frame, text="Select Device", padding=10)
        device_frame.pack(fill=tk.X, pady=(0, 10))

        self.device_combo = ttk.Combobox(device_frame, state="readonly", width=60)
        self.device_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)

        self.device_info_label = ttk.Label(device_frame, text="")
        self.device_info_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(device_frame, text="Set VID/PID", command=self.set_device_identity).pack(side=tk.RIGHT)
        self.device_identity_label = ttk.Label(main_frame, text="", wraplength=1050)
        self.device_identity_label.pack(fill=tk.X, pady=(0, 5))

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

        function_frame = ttk.Frame(assign_frame)
        function_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        function_frame.rowconfigure(0, weight=1)
        function_frame.columnconfigure(0, weight=1)

        self.function_tree = ttk.Treeview(
            function_frame, columns=("Function", "Input", "Device"),
            show="headings", selectmode="browse", height=15
        )
        for column, width in (("Function", 150), ("Input", 120), ("Device", 160)):
            self.function_tree.heading(column, text=column)
            self.function_tree.column(column, width=width, minwidth=80)
        self.function_tree.grid(row=0, column=0, sticky="nsew")
        self.function_tree.bind("<Double-1>", self.on_binding_double_click)
        self.function_tree.bind("<<TreeviewSelect>>", self.on_function_selected)
        scrollbar = ttk.Scrollbar(function_frame, orient=tk.VERTICAL,
                                  command=self.function_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.function_tree.configure(yscrollcommand=scrollbar.set)
        self.function_tree.tag_configure("assigned", foreground="#176b32")
        self.function_tree.tag_configure("unassigned", foreground="#666666")
        for code, name in FLIGHT_FUNCTIONS:
            self.function_tree.insert(
                "", tk.END, iid=code, values=(name, "Not assigned", ""),
                tags=("unassigned",)
            )

        # Modifiers
        mod_frame = ttk.LabelFrame(assign_frame, text="Modifiers", padding=5)
        mod_frame.pack(fill=tk.X, pady=5)

        self.reverse_var = tk.BooleanVar()
        self.convert_var = tk.BooleanVar()

        self.reverse_check = ttk.Checkbutton(
            mod_frame, text=":R - Reverse/Invert axis", variable=self.reverse_var,
            command=self.on_modifiers_changed, state="disabled"
        )
        self.reverse_check.pack(anchor=tk.W)
        self.convert_check = ttk.Checkbutton(
            mod_frame, text=":C - Convert range (for throttle)", variable=self.convert_var,
            command=self.on_modifiers_changed, state="disabled"
        )
        self.convert_check.pack(anchor=tk.W)

        self.modifier_status = ttk.Label(mod_frame, text="Select a function to view its modifiers", wraplength=400)
        self.modifier_status.pack(anchor=tk.W, pady=(5, 0))
        self.assign_status = ttk.Label(assign_frame, text="Select a function, then click an axis or button")
        self.assign_status.pack(pady=5)

    def on_function_selected(self, event=None):
        """Show modifiers of the selected assignment; disable them for empty rows."""
        selection = self.function_tree.selection()
        data = self.assignments.get(selection[0]) if selection else None
        modifiers = data.get('modifiers', '').split(':') if data else []
        self.reverse_var.set('R' in modifiers)
        self.convert_var.set('C' in modifiers)
        state = '!disabled' if data else 'disabled'
        self.reverse_check.state([state])
        self.convert_check.state([state])
        if data:
            self.modifier_status.config(text=(
                f"Current assignment: {data['input']}{data['modifiers']} | "
                f"Invert: {'On' if self.reverse_var.get() else 'Off'} | "
                f"Convert range: {'On' if self.convert_var.get() else 'Off'}"
            ))
        elif selection:
            self.modifier_status.config(text="Not assigned - assign an input to enable modifiers")
        else:
            self.modifier_status.config(text="Select a function to view its modifiers")

    def on_modifiers_changed(self):
        """Apply checkbox changes directly to the selected existing assignment."""
        selection = self.function_tree.selection()
        data = self.assignments.get(selection[0]) if selection else None
        if not data:
            self.on_function_selected()
            return
        modifiers = [part for part in data['modifiers'].split(':') if part and part not in ('R', 'C')]
        if self.reverse_var.get():
            modifiers.append('R')
        if self.convert_var.get():
            modifiers.append('C')
        data['modifiers'] = ''.join(':' + part for part in modifiers)
        self.update_function_assignments()

    # =========================================================================
    # Device Management
    # =========================================================================

    def refresh_devices(self):
        """Refresh and display detected devices"""
        self.monitor.refresh()

        # Update combo boxes
        device_names = []

        for i, info in enumerate(self.monitor.device_info):
            device_names.append(f"{i}: {info['name'][:50]}")

        # Update combo boxes
        self.device_combo['values'] = device_names
        if device_names:
            self.device_combo.current(0)
            self.on_device_selected(None)
        else:
            self.device_combo.set("")
            self.device_info_label.config(text="No devices connected")
            self.device_identity_label.config(text="")
            self.update_buttons([])

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
            identity = (
                f"VID:{info['vid']:04X} PID:{info['pid']:04X}"
                if info['vid'] and info['pid'] else "VID/PID unavailable"
            )
            self.device_identity_label.config(
                text=f"{identity} | {info['identity_source']} | GUID: {info['guid']}",
                foreground="red" if not info['section_id'] else "#176b32"
            )

    def set_device_identity(self):
        """Let the user explicitly resolve an unsupported GUID for this session."""
        idx = self.device_combo.current()
        if idx < 0 or idx >= len(self.monitor.device_info):
            return
        info = self.monitor.device_info[idx]
        value = simpledialog.askstring(
            "Device identification", "Enter hexadecimal VID:PID (for example 231D:0200).\n"
            "Use IDs from Windows Device Manager. This override lasts until device refresh.",
            parent=self.root
        )
        if value is None:
            return
        match = re.fullmatch(r'\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*', value)
        if not match or not all(int(part, 16) for part in match.groups()):
            messagebox.showerror("Invalid identity", "Enter nonzero four-digit hexadecimal VID:PID values.")
            return
        vid, pid = (int(part, 16) for part in match.groups())
        info.update(vid=vid, pid=pid, section_id=get_ac7_section_id(vid, pid),
                    profile=DEVICE_PROFILES.get((vid, pid)), identity_source='Manual')
        for data in self.assignments.values():
            if data.get('device_index') == idx:
                data['section_id'] = info['section_id']
        self.on_device_selected(None)
        self.update_function_assignments()

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

        self.update_function_assignments()

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

        self.update_function_assignments()
        self.status_label.config(text=f"Applied {applied} device profiles")

        if applied > 0:
            if messagebox.askyesno("Save?", f"Applied {applied} profiles.\nSave to Input.ini now?"):
                self.save_config()

    # =========================================================================
    # Monitor Tab Functions
    # =========================================================================

    def schedule_monitor_update(self):
        """Poll inputs on the Tkinter main thread at approximately 30 Hz."""
        self.monitor_after_id = None
        if not self.running:
            return
        try:
            self.update_live_monitor()
        except Exception as exc:
            self.status_label.config(text=f"Monitor error: {exc}")
        finally:
            if self.running:
                self.monitor_after_id = self.root.after(33, self.schedule_monitor_update)

    def update_buttons(self, buttons):
        """Keep canvas items and update only buttons whose state changed."""
        if len(self.button_items) != len(buttons):
            self.button_canvas.delete("all")
            self.button_items = []
            self.button_states = [None] * len(buttons)
            cols, size, pad = 8, 30, 5
            for i in range(len(buttons)):
                row, col = divmod(i, cols)
                x, y = col * (size + pad) + pad, row * (size + pad) + pad
                item = self.button_canvas.create_rectangle(
                    x, y, x + size, y + size, fill="#E0E0E0", outline="#333"
                )
                self.button_items.append(item)
                self.button_canvas.create_text(x + size // 2, y + size // 2, text=str(i + 1))

        for i, pressed in enumerate(buttons):
            if self.button_states[i] != pressed:
                self.button_canvas.itemconfigure(
                    self.button_items[i], fill="#4CAF50" if pressed else "#E0E0E0"
                )
                self.button_states[i] = pressed

    def update_live_monitor(self):
        """Update live input display"""
        idx = self.device_combo.current()
        if idx < 0:
            self.update_buttons([])
            return

        state = self.monitor.get_state(idx)
        if not state:
            self.update_buttons([])
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

        self.update_buttons(state['buttons'])

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
        selection = self.function_tree.selection()
        if not selection:
            self.assign_status.config(text="Select a function first!", foreground="red")
            return

        func_code = selection[0]

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

        self.update_function_assignments()
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
            self.loaded_bindings.clear()
            self.loaded_sections.clear()
            current_section = None
            current_name = None

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    section = line[1:-1]
                    current_section = section if section.startswith('Joystick-') else None
                    current_name = None
                elif line.startswith('ProductName='):
                    current_name = line.split('=', 1)[1].strip().strip('"')
                elif line.startswith('Flight_') and '=' in line and current_section:
                    parts = line.split('=', 1)
                    func, value = parts[0].strip(), parts[1].strip()
                    self.loaded_bindings.add((current_section, func))
                    if value:
                        # Parse modifiers
                        if ':' in value:
                            p = value.split(':')
                            input_str = p[0]
                            mods = ':' + ':'.join(p[1:])
                        else:
                            input_str = value
                            mods = ""

                        self.loaded_sections[func] = current_section
                        self.assignments[func] = {
                            'device_name': current_name or "Unknown",
                            'section_id': current_section,
                            'input': input_str,
                            'modifiers': mods,
                        }

            self.update_function_assignments()
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

        unresolved = [
            f"{func}: {data.get('device_name', 'Unknown')}"
            for func, data in self.assignments.items()
            if not isinstance(data.get('section_id'), str) or not re.fullmatch(
                r'Joystick-[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}',
                data['section_id']
            )
        ]
        if unresolved:
            messagebox.showerror(
                "Device identification required",
                "Nothing was saved. Resolve the device identity for these bindings:\n\n"
                + "\n".join(unresolved) + "\n\nSelect the device and use Set VID/PID."
            )
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

            # Remove only bindings deleted or moved since the last load.
            removed = set()
            for sec, func in self.loaded_bindings:
                data = self.assignments.get(func)
                if data is None or (
                    self.loaded_sections.get(func) == sec
                    and data.get('section_id') != sec
                ):
                    removed.add((sec, func))

            new_lines = []
            current_section = None
            seen_sections = set()
            written = set()

            def append_missing_bindings():
                for func, value in sections.get(current_section, {}).items():
                    if (current_section, func) not in written:
                        if new_lines and not new_lines[-1].endswith('\n'):
                            new_lines[-1] += '\n'
                        new_lines.append(f"{func}={value}\n")
                        written.add((current_section, func))

            for line in lines:
                stripped = line.strip()
                if stripped.startswith('[') and stripped.endswith(']'):
                    append_missing_bindings()
                    current_section = stripped[1:-1]
                    seen_sections.add(current_section)

                if current_section and current_section.startswith('Joystick-'):
                    if stripped.startswith('Flight_') and '=' in stripped:
                        func = stripped.split('=', 1)[0].strip()
                        if (current_section, func) in removed:
                            # Empty the binding explicitly so AC7 cannot reuse it.
                            new_lines.append(f"{func}=\n")
                            continue
                        if func in sections.get(current_section, {}):
                            new_lines.append(f"{func}={sections[current_section][func]}\n")
                            written.add((current_section, func))
                            continue
                new_lines.append(line)

            append_missing_bindings()
            for sec, bindings in sections.items():
                if sec in seen_sections:
                    continue
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] += '\n'
                new_lines.append(f"\n[{sec}]\n")
                name = next(
                    data.get('device_name', 'Unknown')
                    for data in self.assignments.values() if data.get('section_id') == sec
                )
                new_lines.append(f'ProductName="{name}"\n')
                for func, value in bindings.items():
                    new_lines.append(f"{func}={value}\n")

            with open(self.config_path, 'w') as f:
                f.writelines(new_lines)

            self.loaded_bindings = {
                (sec, func) for sec, bindings in sections.items() for func in bindings
            } | (self.loaded_bindings - removed)
            self.loaded_sections = {
                func: data.get('section_id') for func, data in self.assignments.items()
            }

            self.status_label.config(text="Saved!")
            messagebox.showinfo("Success", f"Saved to:\n{self.config_path}\n\nRestart AC7 to apply changes.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def update_function_assignments(self):
        """Refresh assignment feedback without replacing rows or selection."""
        for code, name in FLIGHT_FUNCTIONS:
            data = self.assignments.get(code)
            if data:
                values = (
                    name, data['input'] + data['modifiers'],
                    data.get('device_name', 'Unknown')
                )
                tags = ("assigned",)
            else:
                values = (name, "Not assigned", "")
                tags = ("unassigned",)
            self.function_tree.item(code, values=values, tags=tags)
        self.on_function_selected()

    def on_binding_double_click(self, event):
        """Delete binding on double-click"""
        func = self.function_tree.identify_row(event.y)
        if func:
            if func in self.assignments:
                if messagebox.askyesno("Delete?", f"Remove binding for {func}?"):
                    del self.assignments[func]
                    self.update_function_assignments()

    def clear_bindings(self):
        """Clear all bindings"""
        if messagebox.askyesno("Confirm", "Clear all bindings?"):
            self.assignments.clear()
            self.update_function_assignments()

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
        if self.monitor_after_id is not None:
            self.root.after_cancel(self.monitor_after_id)
            self.monitor_after_id = None
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
