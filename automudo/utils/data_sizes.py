import math

DATA_SIZE_SI_STRINGS = ['B', 'kB', 'MB', 'GB', 'TB']
DATA_SIZE_SI_STRINGS_LOWERCASE = [str.lower(s) for s in DATA_SIZE_SI_STRINGS]
DATA_SIZE_IEC_STRINGS = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
DATA_SIZE_IEC_STRINGS_LOWERCASE = [str.lower(s) for s in DATA_SIZE_IEC_STRINGS]


def parse_data_size_string(data_size_string, assume_unit_confusion=True):
    data_size, data_size_unit = data_size_string.split()
    data_size = float(data_size)
    data_size_unit = data_size_unit.lower()

    if data_size_unit in DATA_SIZE_IEC_STRINGS_LOWERCASE:
        base = 1024
        power = DATA_SIZE_IEC_STRINGS_LOWERCASE.index(data_size_unit)
    elif data_size_unit in DATA_SIZE_SI_STRINGS_LOWERCASE:
        base = 1000
        power = DATA_SIZE_SI_STRINGS_LOWERCASE.index(data_size_unit)

    if assume_unit_confusion:
        base = 1024

    return math.ceil(data_size * (base ** power))


def build_data_size_string(data_size, use_iec_units=True):
    if use_iec_units:
        base = 1024
        units_strings = DATA_SIZE_IEC_STRINGS
    else:
        base = 1000
        units_strings = DATA_SIZE_SI_STRINGS

    for unit_string in units_strings:
        if data_size < base:
            return "{:.2f} {}".format(data_size, unit_string)
        data_size /= base
    raise ValueError("Unexpectedly big data size: {}".format(data_size))
