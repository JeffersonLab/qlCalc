import logging
from qlCalc.cryocavity import Cryocavity
import time
import os
import threading
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

# Create a signaling event that we are exiting.  This will be used to coordinate shutdown of threads, CA monitors, etc.
shutdown_event = threading.Event()


# Setup a signal handler to gracefully shutdown the application.  Threads should be watching this event and gracefully
# stop
def sig_handler(signum, frame):
    if signum in (1, 2, 3, 15):
        logger.info("receeved signal '%d' - gracefully terminating.", signum)
        shutdown_event.set()


def process_new_data(cav_dict, update_queue, req_queue, event):
    while not event.is_set() or not update_queue.empty():
        cav_name = update_queue.get()
        logger.debug("process_new_data thread received cavity '%s'", cav_name)
        cav_dict[cav_name].process_new_data()
        logger.debug("process_new_data thread finished new cavity data %s", cav_name)
        logger.debug("process_new_data thread writing '%s' to request_queue", cav_name)
        req_queue.put(cav_name)


def request_new_data(cav_dict, req_queue, delay, event):
    while not event.is_set() or not req_queue.empty():
        cav_name = req_queue.get()
        logger.debug("request_new_data thread received cavity '%s'", cav_name)
        # This method will request that new data be collected
        cav_dict[cav_name].request_new_data(delay)
        logger.debug("request_new_data thread made request for '%s'", cav_name)


def main():
    logger.info("{} {} beginning execution".format(app_name, app_version))

    # Queue for tracking which cavities have new data available and for tracking future requests.  maxsize=1000 since
    # that is roughly twice the max number of cavities.  Should only ever have one active entry for each cavity, and
    # this provides a nice safety margin.
    update_queue = queue.Queue(maxsize=1000)
    request_queue = queue.Queue(maxsize=1000)

    # cav_names = ("VL26-7", "VL26-8")
    cav_names = ("VL26-7",)
    cav_dict = {}
    for cav in cav_names:
        logger.debug("About to create_cryocavity %s", cav)
        cc = Cryocavity.create_cryocavity(cav, update_queue=update_queue, shutdown_event=shutdown_event,
                                          epics_prefix="adamc:")
        cav_dict[cav] = cc
        logger.debug("About to trigger data collection on %s", cc.cavity_name)

    for cc in cav_dict:
        cav_dict[cc].trigger_data_collection()

    # Start a thread that will process the data associated with a new set of data for an individual cavity
    request_thread = threading.Thread(target=request_new_data, args=(cav_dict, request_queue, 1, shutdown_event))
    request_thread.start()
    update_thread = threading.Thread(target=process_new_data,
                                     args=(cav_dict, update_queue, request_queue, shutdown_event))
    update_thread.start()

    # Now hangout, waiting to receive a signal that will trigger a shutdown
    update_thread.join()
    request_thread.join()


if __name__ == '__main__':
    main()
