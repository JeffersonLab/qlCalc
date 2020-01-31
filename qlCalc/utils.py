def get_epics_cavity_name(ced_name):
    # TODO: pull this info from the CED and don't bother with a static mapper function
    mapper = {
        'VL26-7': 'RVQ7',
        'VL26-8': 'RVQ8',
    }

    return mapper[ced_name]
