import logging
from qlCalc.cryocavity import Cryocavity
import time
import os
import threading
import queue
import signal
from sortedcontainers import SortedList

# Setup basic app information and environment
app_name = 'qlCalc'
app_version = 'v0.1'
app_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

# Set up global logging defaults
log_level = logging.DEBUG
log_file = os.path.join(app_dir, "log", "qlCalc.log")
logging.basicConfig(level=log_level, filename=log_file, filemode='a', datefmt="%Y-%m-%d %H:%M:%S.%1s %Z",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Get a logger for this module
logger = logging.getLogger(app_name)

# Create a signaling event that we are exiting.  This will be used to coordinate shutdown of threads, CA monitors, etc.
shutdown_event = threading.Event()


def sig_handler(signum, frame):
    """Method to handle a number of signals that indicate shutdown request"""
    logger.info("received signal '%s' - gracefully terminating.", signum)
    shutdown_event.set()


def process_new_data(cav_dict, update_queue, req_queue, event):
    """Callable meant to be run in own thread to handle the processing of new data
        Args:
            cav_dict (dict): A dictionary of cavity names to Cryocavity objects
            update_queue (queue.Queue): The queue from which CavityTasks will be read
            req_queue (queue.Queue): The queue to which CavityTasks will be written to after processing associated data.
            event (threading.Event): Event used to signal application shutdown
    """
    while not event.is_set() or not update_queue.empty():
        logger.debug("Top of process_new_data loop.  event.is_set = %s", str(event.is_set()))
        cavity_task = update_queue.get()
        cavity_name = cavity_task.cavity_name
        logger.debug("process_new_data thread received cavity '%s'", cavity_name)
        cav_dict[cavity_name].process_new_data()
        logger.debug("process_new_data thread finished new cavity data %s", cavity_name)
        logger.debug("process_new_data thread writing '%s' to request_queue", cavity_name)
        req_queue.put(cavity_task)

    logger.debug("process_new_data method has exited")


def request_new_data(cav_dict, req_queue, event):
    """Callable meant to be run in own thread to handle the scheduling of making the next data request for a cavity
        Args:
            cav_dict (dict): A dictionary of cavity names to Cryocavity objects
            req_queue (queue.Queue): The queue from which cavity tasks are read
            event (threading.Event): An event used to signal application shutdown
            """

    # Sort the requests according to the time at which the request should occur.  Earlier times first.
    # TODO: The order on this sorting may need to be reversed.  Check it out
    schedule = SortedList(key=lambda x: x.request_timestamp)
    while not event.is_set() or not req_queue.empty() or len(schedule) != 0:
        logger.debug("Top of request_new_data loop.  event.is_set = %s", str(event.is_set()))
        # We don't have anything in the schedule, so just wait on the next item to arrive in the queue
        if len(schedule) == 0:
            # TODO: is this timeout actually needed here?
            get_cavity_notification(req_queue, schedule, 15)

        # We have something in the queue.  It may be time to make the request.  If so do it, if not try to get something
        # from the queue until it is time to make that request.
        if len(schedule) != 0:
            # Should always assign to next_req since len(schedule) > 0.  Assignment here to quiet IDE warnings
            next_req = None
            for req in schedule:
                next_req = req
                break
            next_req_ts = next_req.request_timestamp
            if next_req_ts <= time.time():
                # Remove the notice from the schedule and make the request
                schedule.pop(0)
                cav_dict[next_req.cavity_name].request_new_data()
            else:
                to = next_req_ts - time.time()
                get_cavity_notification(req_queue, schedule, to)

    logger.debug("at end of request_new_data method/thread")


def get_cavity_notification(req_queue, schedule, timeout=None):
    """Attempts to read from request queue (with timeout) and adds the request to the 'schedule' data structure.

        Args:
            req_queue (queue.Queue):  The queue from which to read the next CavityNotification
            schedule (sortedcontainers.SortedList): The sorted list representing the request schedule
            timeout (float): How long to attempt to read from the queue.  None for infinite wait

        Returns (None):  Returns nothing
    """
    try:
        cav = req_queue.get(timeout=timeout)
        logger.debug("Read (%s, %f) from request_queue.", cav.cavity_name, cav.request_timestamp)
        schedule.add(cav)
        logger.debug("Added (%s, %f) to schedule.", cav.cavity_name, cav.request_timestamp)
    except queue.Empty:
        # Timeout causes an exception to be thrown.  Just continue on.
        logger.debug("req_queue.get timed out after %d seconds.", timeout)


# TODO: Need to add thread that sleeps for a while (maybe 10 seconds?) and then iterates over Cryocavity objects to see
# when the last request was made and if we're still waiting on it.  If we'e been waiting longer than a timeout,
# re-trigger the request and write out NaN's as results.
def main():
    logger.info("{} {} beginning execution".format(app_name, app_version))

    # Attach the "shutdown" signal handler to appropriate signals
    signal.signal(signal.SIGHUP, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGQUIT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # Queue for tracking which cavities have new data available and for tracking future requests.  maxsize=1000 since
    # that is roughly twice the max number of cavities.  Should only ever have one active entry for each cavity, and
    # this provides a nice safety margin.
    update_queue = queue.Queue(maxsize=1000)
    request_queue = queue.Queue(maxsize=1000)

    # TODO: Setup dev soft IOC for writing out results
    # Various "pre-built" lists for testing - my dev soft FCC IOC has zones TL02 - TL26 and VL02 - VL26
    # cav_names = ("VL26-7", "VL26-8")
    # cav_names = ("VL26-7",)
    cav_names = ("VL26-1", "VL26-2", "VL26-3", "VL26-4", "VL26-5", "VL26-6", "VL26-7", "VL26-8")

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
    request_thread = threading.Thread(target=request_new_data, args=(cav_dict, request_queue, shutdown_event))
    request_thread.start()
    update_thread = threading.Thread(target=process_new_data,
                                     args=(cav_dict, update_queue, request_queue, shutdown_event))
    update_thread.start()

    # Now hangout, waiting to receive a signal that will trigger a shutdown
    update_thread.join()
    request_thread.join()

    logger.debug("main routine exiting.")


if __name__ == '__main__':
    main()
