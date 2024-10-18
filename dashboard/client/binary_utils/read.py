import struct
import json
import math

# Configuration des PXX
PXX_CONFIG = {
    'P00': ('config_file_version', '>H', (0, 50000), 0),  # Unsigned short (2 bytes)
    'P01': ('config_file_date', '>20s', None, '2024/01/01-00:00:00'),  # String (20 bytes)
    'P02': ('search_duration', '>H', (10, 200), 30),  # Unsigned short (2 bytes)
    'P03': ('start_meas_duration', '>H', (10, 200), 60),  # Unsigned short (2 bytes)
    'P04': ('stop_meas_duration', '>H', (10, 200), 60),  # Unsigned short (2 bytes)
    'P05': ('PPG_led_on_duration', '>H', (69, 118, 215, 411), 411),  # Unsigned short (2 bytes)
    'P06': ('PPG_avg_sampling', '>H', (1, 2, 4, 8, 16, 32), 1),  # Unsigned short (2 bytes)
    'P07': ('PPG_sample_rate', '>H', (50, 100, 200, 400, 800), 100),  # Unsigned short (2 bytes)
    'P08': ('PPG_red_current', '>H', (0, 51), 20),  # Unsigned short (2 bytes)
    'P09': ('PPG_ir_current', '>H', (0, 51), 20),  # Unsigned short (2 bytes)
    'P10': ('PPG_green_current', '>H', (0, 51), 20),  # Unsigned short (2 bytes)
    'P11': ('audio_sample_rate', '>H', (1, 10), 4),  # Unsigned short (2 bytes)
    'P12': ('accel_sensitivity', '>H', (2, 4, 8, 16), 4),  # Unsigned short (2 bytes)
    'P13': ('accel_avg_sampling', '>H', (1, 2, 4, 8, 16, 32, 64, 128), 1),  # Unsigned short (2 bytes)
    'P14': ('accel_sample_rate', '>H', (12.5, 25, 50, 100), 25),  # Unsigned short (2 bytes)
    'P15': ('odba_duration', '>H', (1, 5), 1),  # Unsigned short (2 bytes)
    'P16': ('spo2_avg_sampling', '>H', (1, 20), 5),  # Unsigned short (2 bytes)
    'P17': ('spo2_err_detection', '>H', (1, 100), 5),  # Unsigned short (2 bytes)
    'P18': ('hr_avg_sampling', '>H', (1, 20), 5),  # Unsigned short (2 bytes)
    'P19': ('hr_err_detection', '>H', (1, 100), 30),  # Unsigned short (2 bytes)
}

# Configuration des MXX
MXX_CONFIG = {
    'M00': ('timestamp', '>I', 4, 0),  # Unsigned int (4 bytes)
    'M01': ('battery', '>B', 1, 0),  # Unsigned byte (1 byte)
    'M02': ('integrity', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M03': ('spo2', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M04': ('heart_rate', '>B', 1, 0),  # Unsigned byte (1 byte)
    'M05': ('odba', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M06': ('audio_sp1', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M07': ('audio_sp2', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M08': ('audio_sp3', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M09': ('audio_sp4', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M10': ('audio_sp5', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M11': ('audio_sp6', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M12': ('audio_sp7', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M13': ('audio_sp8', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M14': ('audio_sp9', '>H', 2, 0),  # Unsigned short (2 bytes)
    'M15': ('audio_sp10', '>H', 2, 0),  # Unsigned short (2 bytes)
}

def read_binary_file(data):

    file_size = len(data)

    ## DEBUG
    # print(f"File size: {file_size} bytes")

    timestamp_start = struct.unpack_from('>I', data, 0x00)[0]
    timestamp_stop = struct.unpack_from('>I', data, 0x04)[0]
    version = struct.unpack_from('>H', data, 0x08)[0]

    ## DEBUG
    # print(f"TIMESTAMP START: {timestamp_start}")
    # print(f"TIMESTAMP STOP: {timestamp_stop}")
    # print(f"VERSION: {version}")

    # Extraction des configurations PXX
    pta = {}
    offset = 0x0A
    for key, (name, fmt, _, _) in PXX_CONFIG.items():
        size = struct.calcsize(fmt)
        value = struct.unpack_from(fmt, data, offset)[0]
        if type(value) == bytes:
            value = value.decode('latin-1')[:-1]
        pta[name] = value
        offset += size

    # Lecture des mesures
    measures = []
    measure_size = sum([struct.calcsize(fmt) for _, (name, fmt, size, _) in MXX_CONFIG.items()])
    measures_start_offset = 0x50

    ## DEBUG
    # print(f"Measure size: {measure_size} bytes")
    # print(f"Measures start offset: {measures_start_offset} bytes")

    measures_count  = math.ceil((timestamp_stop - timestamp_start))

    for i in range(measures_count + 1):
        measure_offset = measures_start_offset + i * measure_size
        if measure_offset + measure_size > file_size:
            print(f"Skipping measure at offset {measure_offset}, exceeds file size")
            break
        measure = {}
        for key, (name, fmt, size, _) in MXX_CONFIG.items():
            value = struct.unpack_from(fmt, data, measure_offset)[0]
            measure[name] = value
            measure_offset += size
        measures.append(measure)

    ## DEBUG
    # print("Number of measures read:", len(measures))
    # print("Measures:")
    # for measure in measures:
    #     print(measure)

    # Détection du footer (32 octets de FF)
    footer_offset = measure_offset + 32

    ## DEBUG
    # print(f"Footer offset: {footer_offset} bytes")

    json_data = data[footer_offset:].decode('latin-1')
    config = json.loads(json_data)

    ## DEBUG
    # print("Configuration JSON:")
    # print(json.dumps(config, indent=4))

    result = {
        'timestamp_start': timestamp_start,
        'timestamp_stop': timestamp_stop,
        'version': version,
        'pta': pta,
        'measures': measures,
        'config': config,
    }

    return result
