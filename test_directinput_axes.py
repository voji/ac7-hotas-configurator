import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import ac7_configurator as app
from directinput_axes import select_axis_names


class DirectInputAxesTests(unittest.TestCase):
    def test_sparse_and_full_device_layouts(self):
        layouts = [dict(section_id='pedal', axes=['X', 'Z', 'Slider1']),
                   dict(section_id='stick', axes=['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz'])]
        self.assertEqual(select_axis_names(layouts, 'pedal', 3), ['X', 'Z', 'Slider1'])
        self.assertEqual(select_axis_names(layouts, 'stick', 6), layouts[1]['axes'])

    def test_missing_mismatched_and_conflicting_layouts_are_rejected(self):
        layouts = [dict(section_id='device', axes=['X', 'Z'])]
        self.assertEqual(select_axis_names(layouts, 'missing', 2), [None, None])
        self.assertEqual(select_axis_names(layouts, 'device', 3), [None] * 3)
        layouts.append(dict(section_id='device', axes=['X', 'Y']))
        self.assertEqual(select_axis_names(layouts, 'device', 2), [None, None])

    def make_controller(self):
        controller = app.AC7Configurator.__new__(app.AC7Configurator)
        controller.axis_name_labels = [Mock() for _ in range(8)]
        controller.axis_assign_buttons = [Mock() for _ in range(8)]
        controller.function_tree = Mock()
        controller.function_tree.selection.return_value = ('Flight_Yaw',)
        controller.device_combo = Mock()
        controller.device_combo.current.return_value = 0
        controller.monitor = SimpleNamespace(device_info=[
            dict(axis_names=['X', 'Z', 'Slider1'], name='T-Rudder', section_id='pedal')])
        controller.reverse_var = Mock()
        controller.reverse_var.get.return_value = False
        controller.convert_var = Mock()
        controller.convert_var.get.return_value = False
        controller.assignments = {}
        controller.assign_status = Mock()
        controller.update_function_assignments = Mock()
        return controller

    def test_display_and_assignment_use_same_sparse_axis(self):
        controller = self.make_controller()
        controller.update_axis_controls(['X', 'Z', 'Slider1'])
        for index, name in enumerate(['X', 'Z', 'Slider1']):
            controller.axis_name_labels[index].config.assert_called_with(text=name + ':')
            controller.assign_input('axis', index)
            self.assertEqual(controller.assignments['Flight_Yaw']['input'], name)
        controller.axis_assign_buttons[3].state.assert_called_with(['disabled'])
        controller.update_axis_controls(['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz'])
        controller.axis_name_labels[1].config.assert_called_with(text='Y:')

    def test_unknown_axis_cannot_be_assigned(self):
        controller = self.make_controller()
        controller.monitor.device_info[0]['axis_names'] = [None] * 3
        controller.update_axis_controls([None] * 3)
        controller.axis_name_labels[1].config.assert_called_with(text='Axis 1:')
        controller.axis_assign_buttons[1].state.assert_called_with(['disabled'])
        for index in (-1, 0, 3):
            controller.assign_input('axis', index)
        self.assertFalse(controller.assignments)
        controller.update_axis_controls([])
        controller.axis_name_labels[0].config.assert_called_with(text='N/A:')


if __name__ == '__main__':
    unittest.main()
