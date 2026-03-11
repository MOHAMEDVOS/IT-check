"""
mic.py — Reads the default Windows microphone name and static volume level.
Uses pycaw + Windows Core Audio API. No recording, no audio capture.
"""

import comtypes
import ctypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from pycaw.constants import EDataFlow, ERole


def check_mic_level(callback=None) -> dict:
    """Get the default microphone name and its static volume level (0-100)."""
    comtypes.CoInitialize()
    try:
        # Get the default capture (microphone) device directly
        device_enumerator = AudioUtilities.GetDeviceEnumerator()
        default_device = device_enumerator.GetDefaultAudioEndpoint(
            EDataFlow.eCapture.value,   # eCapture = microphone input
            ERole.eConsole.value        # eConsole = default system device
        )

        # Read the friendly name and enumerator type using pycaw's own PROPERTYKEY definition
        device_name = "Unknown Microphone"
        device_type = "Unknown Type"
        try:
            from pycaw.api.mmdeviceapi.depend.structures import PROPERTYKEY
            from comtypes import GUID

            props = default_device.OpenPropertyStore(0)  # STGM_READ

            # 1. Friendly Name
            pkey_name = PROPERTYKEY()
            pkey_name.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
            pkey_name.pid = 14   # PKEY_Device_FriendlyName

            name_var = props.GetValue(ctypes.byref(pkey_name))
            name = name_var.GetValue()
            if name:
                device_name = str(name)

            # 2. Enumerator Name (Bus type)
            pkey_enum = PROPERTYKEY()
            pkey_enum.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
            pkey_enum.pid = 24  # PKEY_Device_EnumeratorName

            enum_var = props.GetValue(ctypes.byref(pkey_enum))
            enum_name = enum_var.GetValue()
            
            # 3. Device Description (for distinguishing Built-in vs Aux)
            pkey_desc = PROPERTYKEY()
            pkey_desc.fmtid = GUID("{a45c254e-df1c-4efd-8020-67d146a850e0}")
            pkey_desc.pid = 2   # PKEY_Device_DeviceDesc
            
            desc_var = props.GetValue(ctypes.byref(pkey_desc))
            desc_name = desc_var.GetValue()

            if enum_name:
                val = str(enum_name).upper()
                if "USB" in val:
                    device_type = "USB"
                elif "BTH" in val:
                    device_type = "Bluetooth"
                else:
                    device_type = "Aux"
                    if desc_name:
                        desc_val = str(desc_name).upper()
                        if "ARRAY" in desc_val or "INTERNAL" in desc_val or "BUILT" in desc_val:
                            device_type = "Built-in"

        except Exception as e:
            pass

        # Read volume level
        interface = default_device.Activate(
            IAudioEndpointVolume._iid_,
            comtypes.CLSCTX_INPROC_SERVER,
            None
        )
        volume_ctrl = interface.QueryInterface(IAudioEndpointVolume)
        level = round(volume_ctrl.GetMasterVolumeLevelScalar() * 100)

        return {
            "device_name": device_name,
            "device_type": device_type,
            "level":       level,
            "error":       None
        }

    except Exception as e:
        return {
            "device_name": "Unknown Microphone",
            "device_type": "Unknown Type",
            "level":       0,
            "error":       str(e)
        }
    finally:
        comtypes.CoUninitialize()


def set_mic_level(target_level=1.0) -> bool:
    """Set the default microphone volume to target_level (0.0 to 1.0)."""
    comtypes.CoInitialize()
    try:
        device_enumerator = AudioUtilities.GetDeviceEnumerator()
        default_device = device_enumerator.GetDefaultAudioEndpoint(
            EDataFlow.eCapture.value, ERole.eConsole.value
        )
        interface = default_device.Activate(
            IAudioEndpointVolume._iid_, comtypes.CLSCTX_INPROC_SERVER, None
        )
        volume_ctrl = interface.QueryInterface(IAudioEndpointVolume)
        volume_ctrl.SetMasterVolumeLevelScalar(target_level, None)
        return True
    except Exception:
        return False
    finally:
        comtypes.CoUninitialize()


if __name__ == "__main__":
    r = check_mic_level()
    if r["error"]:
        print(f"Error: {r['error']}")
    else:
        print(f"Device : {r['device_name']}")
        print(f"Level  : {r['level']} / 100")