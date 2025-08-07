import sounddevice as sd


def get_input_device_by_name(name_keyword="USB"):
    """
    Returns the index of the first input-capable device matching the given keyword.

    Args:
        name_keyword (str): Substring to match in device name (case-insensitive).

    Returns:
        int: Index of matching input device.

    Raises:
        RuntimeError: If no matching input device is found.
    """
    for i, dev in enumerate(sd.query_devices()):
        if name_keyword.lower() in dev['name'].lower() and dev['max_input_channels'] > 0:
            return i
    raise RuntimeError(f"No input device found matching '{name_keyword}'")


def get_output_device_by_name(name_keyword="USB"):
    """
    Returns the index of the first output-capable device matching the given keyword.

    Args:
        name_keyword (str): Substring to match in device name (case-insensitive).

    Returns:
        int: Index of matching output device.

    Raises:
        RuntimeError: If no matching output device is found.
    """
    for i, dev in enumerate(sd.query_devices()):
        if name_keyword.lower() in dev['name'].lower() and dev['max_output_channels'] > 0:
            return i
    raise RuntimeError(f"No output device found matching '{name_keyword}'")

# try:
#     mic_index = get_input_device_by_name("usb audio device")
#     speaker_index = get_output_device_by_name("usb")
#     print(f"Using mic at index {mic_index}")
#     print(f"Using speaker at index {speaker_index}")
# except RuntimeError as e:
#     print("Device error:", e)
