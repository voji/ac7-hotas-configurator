import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ac7_configurator as app


class DeviceIdentityTests(unittest.TestCase):
    def test_connected_device_guid_samples(self):
        for guid, ids in (
            ('03002baa1d2300000002000000000000', (0x231D, 0x0200)),
            ('0300f7051d2300001f01000000000000', (0x231D, 0x011F)),
        ):
            with self.subTest(guid=guid):
                self.assertEqual(app.get_guid_vid_pid(guid), ids)

    def test_unknown_guid_layouts_are_not_guessed(self):
        for guid in (None, '', 'x' * 32, '0' * 32,
                     '03000000564b422053696d0000000000',
                     '58496e70757400000000000000000000'):
            with self.subTest(guid=guid):
                self.assertEqual(app.get_guid_vid_pid(guid), (None, None))

    def test_section_id(self):
        self.assertEqual(
            app.get_ac7_section_id(0x231D, 0x0200),
            'Joystick-0200231D-0000-0000-0000-504944564944',
        )

    def test_manual_identity_resolves_current_device_assignments(self):
        controller = app.AC7Configurator.__new__(app.AC7Configurator)
        controller.root = Mock()
        controller.device_combo = Mock()
        controller.device_combo.current.return_value = 0
        controller.monitor = Mock()
        controller.monitor.device_info = [dict(section_id=None)]
        controller.assignments = {
            'Flight_Roll': dict(device_index=0, section_id=None),
            'Flight_Pitch': dict(device_index=1, section_id=None),
        }
        controller.on_device_selected = Mock()
        controller.update_function_assignments = Mock()
        with patch.object(app.simpledialog, 'askstring', return_value='231D:0200'):
            controller.set_device_identity()
        identity = controller.monitor.device_info[0]
        self.assertEqual(identity['identity_source'], 'Manual')
        self.assertEqual(identity['profile'], app.DEVICE_PROFILES[(0x231D, 0x0200)])
        self.assertEqual(controller.assignments['Flight_Roll']['section_id'], identity['section_id'])
        self.assertIsNone(controller.assignments['Flight_Pitch']['section_id'])

    def test_save_rejects_unresolved_binding_without_touching_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'Input.ini'
            original = b'[Other]\r\nKeep=1\r\n'
            path.write_bytes(original)
            controller = app.AC7Configurator.__new__(app.AC7Configurator)
            controller.config_path = str(path)
            for section in (None, '', 'invalid', 'Joystick-injected\n[Other]'):
                controller.assignments = {
                    'Flight_Roll': dict(device_name='Unknown stick', section_id=section,
                                        input='X', modifiers='')
                }
                with self.subTest(section=section), patch.object(app.messagebox, 'showerror') as error:
                    controller.save_config()
                    error.assert_called_once()
                    self.assertIn('Flight_Roll: Unknown stick', error.call_args.args[1])
                    self.assertEqual(path.read_bytes(), original)

    def test_identified_binding_can_be_saved_and_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'Input.ini'
            path.write_text('[Other]\nKeep=1\n')
            controller = app.AC7Configurator.__new__(app.AC7Configurator)
            controller.config_path = str(path)
            controller.loaded_bindings = set()
            controller.loaded_sections = {}
            controller.status_label = Mock()
            controller.update_function_assignments = Mock()
            controller.assignments = {
                'Flight_Roll': dict(device_name='Stick',
                                    section_id=app.get_ac7_section_id(0x231D, 0x0200),
                                    input='X', modifiers=':R')
            }
            with patch.object(app.messagebox, 'showinfo'), patch.object(app.messagebox, 'showerror') as error:
                controller.save_config()
                error.assert_not_called()
                self.assertIn('Flight_Roll=X:R', path.read_text())
                controller.load_config()
                self.assertEqual(controller.assignments['Flight_Roll']['input'], 'X')
                controller.assignments.clear()
                controller.save_config()
                controller.load_config()
                self.assertFalse(controller.assignments)
                self.assertIn('Keep=1', path.read_text())


if __name__ == '__main__':
    unittest.main()
