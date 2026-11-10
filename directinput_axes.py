"""Read DirectInput axis objects without acquiring devices or changing settings."""
import ctypes as c
import os
import uuid
from ctypes import wintypes as w


def select_axis_names(devices, section_id, axis_count):
    """Only accept unambiguous layouts whose axis count matches SDL."""
    layouts = {tuple(d['axes']) for d in devices if d['section_id'] == section_id}
    if len(layouts) != 1:
        return [None] * axis_count
    axes = list(layouts.pop())
    return axes if len(axes) == axis_count else [None] * axis_count


def enumerate_axis_layouts():
    if os.name != 'nt':
        return []
    GUID = c.c_ubyte * 16

    class Device(c.Structure):
        _fields_ = [('size', w.DWORD), ('instance', GUID), ('product', GUID),
                    ('type', w.DWORD), ('name', w.WCHAR * 260),
                    ('productname', w.WCHAR * 260), ('ff', GUID),
                    ('usagepage', w.WORD), ('usage', w.WORD)]

    class Object(c.Structure):
        _fields_ = [('size', w.DWORD), ('guid', GUID), ('offset', w.DWORD),
                    ('type', w.DWORD), ('flags', w.DWORD), ('name', w.WCHAR * 260),
                    ('maxforce', w.DWORD), ('resolution', w.DWORD),
                    ('collection', w.WORD), ('designator', w.WORD),
                    ('usagepage', w.WORD), ('usage', w.WORD),
                    ('dimension', w.DWORD), ('exponent', w.WORD), ('reportid', w.WORD)]

    def method(pointer, index, result, *args):
        table = c.cast(pointer, c.POINTER(c.POINTER(c.c_void_p))).contents
        return c.WINFUNCTYPE(result, c.c_void_p, *args)(table[index])

    axis_guids = {0xa36d02e0: 'X', 0xa36d02e1: 'Y', 0xa36d02e2: 'Z',
                  0xa36d02f4: 'Rx', 0xa36d02f5: 'Ry', 0xa36d02e3: 'Rz'}
    order = ['X', 'Y', 'Z', 'Rx', 'Ry', 'Rz', 'Slider1', 'Slider2']
    object_callback = c.WINFUNCTYPE(w.BOOL, c.POINTER(Object), c.c_void_p)
    device_callback = c.WINFUNCTYPE(w.BOOL, c.POINTER(Device), c.c_void_p)
    layouts = []
    errors = []
    directinput = c.c_void_p()
    kernel = c.WinDLL('kernel32')
    kernel.GetModuleHandleW.restype = c.c_void_p
    iid = GUID.from_buffer_copy(uuid.UUID('bf798031-483a-4da2-aa99-5d64ed369700').bytes_le)
    create = c.WinDLL('dinput8').DirectInput8Create
    create.argtypes = [c.c_void_p, w.DWORD, c.c_void_p, c.POINTER(c.c_void_p), c.c_void_p]
    create.restype = c.c_long
    if create(kernel.GetModuleHandleW(None), 0x800, c.byref(iid), c.byref(directinput), None) < 0:
        raise OSError('DirectInput8Create failed')

    @device_callback
    def visit_device(pointer, context):
        device = c.c_void_p()
        try:
            description = pointer.contents
            hr = method(directinput, 3, c.c_long, c.c_void_p, c.POINTER(c.c_void_p), c.c_void_p)(
                directinput, c.byref(description.instance), c.byref(device), None)
            if hr < 0:
                return 1
            axes = []
            sliders = []

            @object_callback
            def visit_object(pointer, context):
                try:
                    guid = uuid.UUID(bytes_le=bytes(pointer.contents.guid))
                    if str(guid)[8:] != '-c9f3-11cf-bfc7-444553540000':
                        errors.append('Unknown axis GUID')
                        return 1
                    if guid.time_low == 0xa36d02e4:
                        sliders.append('Slider' + str(len(sliders) + 1))
                    elif guid.time_low in axis_guids:
                        axes.append(axis_guids[guid.time_low])
                    else:
                        errors.append('Unknown axis type')
                except Exception as exc:
                    errors.append(str(exc))
                return 1

            hr = method(device, 4, c.c_long, object_callback, c.c_void_p, w.DWORD)(
                device, visit_object, None, 3)  # DIDFT_AXIS
            if hr >= 0:
                axes.extend(sliders)
                if len(set(axes)) == len(axes) and all(a in order for a in axes):
                    # SDL DInput sorts by DIJOYSTATE2 offsets, not enumeration order.
                    layouts.append(dict(
                        section_id='Joystick-' + str(uuid.UUID(bytes_le=bytes(description.product))).upper(),
                        axes=sorted(axes, key=order.index)))
        except Exception as exc:
            errors.append(str(exc))
        finally:
            if device:
                method(device, 2, w.ULONG)(device)
        return 1

    try:
        hr = method(directinput, 4, c.c_long, w.DWORD, device_callback, c.c_void_p, w.DWORD)(
            directinput, 4, visit_device, None, 1)  # GAMECTRL, ATTACHEDONLY
        if hr < 0 or errors:
            raise OSError('DirectInput axis enumeration failed: ' + '; '.join(errors))
        return layouts
    finally:
        method(directinput, 2, w.ULONG)(directinput)
