import logging
from qlCalc.cryocavity import Cryocavity
import time
import os
import queue
import epics
from epics import PV

# Setup basic app information and environment
app_name = 'qlCalc'
app_version = 'v0.1'
app_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
os.environ['EPICS_CA_ADDR_LIST'] = "129.57.228.121"

# Set up global logging defaults
log_level = logging.DEBUG
log_file = os.path.join(app_dir, "log", "qlCalc.log")
logging.basicConfig(level=log_level, filename=log_file, filemode='a', datefmt="%Y-%m-%d %H:%M:%S %Z",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Get a logger for this module
logger = logging.getLogger(app_name)


def main():
    logger.info("{} {} beginning execution".format(app_name, app_version))

    # Queue for tracking which cavities have collected data
    event_queue = queue.Queue(maxsize=1000)

    cav_names = ("VL26-7", "VL26-8")
#    cav_names = ("VL26-7",)
    cav_dict = {}
    for cav in cav_names:
        logger.debug("About to create_cryocavity %s", cav)
        cc = Cryocavity.create_cryocavity(cav, queue=event_queue, epics_prefix="adamc:")
        cav_dict[cav] = cc
        logger.debug("About to trigger data collection on %s", cc.cavity_name)

    for cc in cav_dict:
        cav_dict[cc].trigger_data_collection()


    while True:
        cav_name = event_queue.get()
        print(ascii(cav_dict[cav_name].GETDATA.callbacks))
        logger.debug("Consumer received cavity '%s'", cav_name)
        cav_dict[cav_name].process_new_data(delay=10)
        logger.debug("Finished processing new cavity data %s", cav_name)


if __name__ == '__main__':
    main()
