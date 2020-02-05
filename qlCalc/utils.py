def get_epics_cavity_name(ced_name):
    # TODO: pull this info from the CED and don't bother with a static mapper function
    mapper = {
        'VL26-1': 'RVQ1',
        'VL26-2': 'RVQ2',
        'VL26-3': 'RVQ3',
        'VL26-4': 'RVQ4',
        'VL26-5': 'RVQ5',
        'VL26-6': 'RVQ6',
        'VL26-7': 'RVQ7',
        'VL26-8': 'RVQ8',
    }

    return mapper[ced_name]
