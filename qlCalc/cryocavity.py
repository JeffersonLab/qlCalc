import math
import logging
import time
import epics
from epics import PV

import qlCalc.utils

logger = logging.getLogger(__name__)


# TODO: Add logging of error messages

# noinspection PyPep8Naming
class Cryocavity:
    """A class representing a CEBAF Cryocavity.
    
    This class contains all logic required for calculating its loaded values, including
    querying the control system and other services for data, running calculations, and 
    writing data back to the control system.

    This class contains both a factory method and regular constructor.  Factory method
    should be used in general, but the regular constructor is convenient for test cases.
    """

    @staticmethod
    def create_cryocavity(cavity_name, update_queue, epics_prefix=None):
        # TODO: Update factory to handle more than just C100s
        length = 0.7
        epics_name = qlCalc.utils.get_epics_cavity_name(cavity_name)
        if epics_prefix is not None:
            epics_name = epics_prefix + epics_name
        cavity_type = "c100"
        RQ = 868.9
        GETDATA = epics.PV(epics_name + "GETDATA")
        GMESLQ = epics.PV(epics_name + "GMESLQ")
        CRFPLQ = epics.PV(epics_name + "CRFPLQ")
        CRRPLQ = epics.PV(epics_name + "CRRPLQ")
        DETALQ = epics.PV(epics_name + "DETALQ")
        ITOTLQ = epics.PV(epics_name + "ITOTLQ")
        STARTLQ = epics.PV(epics_name + "STARTLQ")
        ENDLQ = epics.PV(epics_name + "ENDLQ")

        # Set the GETDATA PV to 0 ("disabled") so that we have a known starting point for monitoring, etc.
        GETDATA.put(0)

        logger.debug("About to construct Cryocavity %s.  GETDATA.value = %d", cavity_name, GETDATA.get())

        # Create the cavity object
        return Cryocavity(GETDATA=GETDATA, GMESLQ=GMESLQ, CRFPLQ=CRFPLQ, CRRPLQ=CRRPLQ, DETALQ=DETALQ, ITOTLQ=ITOTLQ,
                          STARTLQ=STARTLQ, ENDLQ=ENDLQ, cavity_name=cavity_name, cavity_type=cavity_type, length=length,
                          RQ=RQ, update_queue=update_queue)

    def get_ced_data(self):
        # TODO: Implement method that get CED data related to the cryocavity and it's parent cryomodule
        pass

    def __init__(self, GETDATA, GMESLQ, CRFPLQ, CRRPLQ, DETALQ, ITOTLQ, STARTLQ, ENDLQ, cavity_name, cavity_type,
                 length, RQ, update_queue):
        """Construct a cryocavity object with references to the appropriate PVs and parameters for the cryocavity
            Args:
                GETDATA (PV): value is the state of the data request process.  (0 = idle, 1 = data requested, 2 = data
                  posted)
                GMESLQ (PV): value is measured cavity gradient in MV/m
                CRFPLQ (PV): value is forward power (uncorrected) in kW
                CRRPLQ (PV): value is reflected power (uncorrected) in kW
                DETALQ (PV): value is relative detune angle in degrees
                ITOTLQ (PV): value is beam current experienced by cavity in uA
                STARTLQ (PV): value is time stamp associated with the start of synchronized data collection
                ENDLQ (PV): value is the time stamp associated with the end synchronized data collection
                cavity_name (str): the CED name of the cavity
                cavity_type (str): type of cavity cell
                length (float): active length of cryocavity in meters
                RQ (float): characteristic shunt impedance in Ohms
                update_queue (queue.Queue): Event queue to which on_GETDATA_change writes
        """
        self.GETDATA = GETDATA
        self.ITOTLQ = ITOTLQ
        self.DETALQ = DETALQ
        self.CRRPLQ = CRRPLQ
        self.CRFPLQ = CRFPLQ
        self.GMESLQ = GMESLQ
        self.STARTLQ = STARTLQ
        self.ENDLQ = ENDLQ
        self.cavity_name = cavity_name
        self.cavity_type = cavity_type
        self.length = length
        self.RQ = RQ
        self.queue = update_queue

        # Hang a callback on the GETDATA monitor so we can have the callback thread notify the main thread of the new
        # data.  None may be used in unit tests - can't add a callback to that.
        if GETDATA is not None:
            self.GETDATA.add_callback(self.on_GETDATA_change)

        # These attributes may/should be calculated at some point later
        self.calc_timestamp = None  #: string: The timestamp when the calculations are run
        self.attenuation_factor = None  #: float: The calculated attenuation factor.  None until calculated
        self.attenuation = None  #: float: The calculated attenuation.  None until calculated
        self.detune_angle = None  #: float: synchronized detune angle (called psi by F. Marhauser) in radians
        self.P_fc = None  #: float: The calculated corrected forward power.  None until calculated
        self.P_rc = None  #: float: The calculated corrected reflected power.  None until calculated
        self.Q_lf = None  #: float: The calculated loaded Q based on forward power.  None until calculated
        self.Q_lr = None  #: float: The calculated loaded Q based on reflected power.  None until calculated
        self.err_msg = []  #: list(string): A list of error messages that may be found during calculations
        self.V_c = None  #: float: cavity voltage in V
        self.P_f = None  #: float: synchronized RF forward power in W
        self.P_r = None  #: float: synchronized RF reflected power in W
        self.I_tot = None  #: float: Total beam current experienced by this cavity in Amps
        self.data_sync_start = None  #: str: time stamp of beginning of the data synchronization process
        self.data_sync_end = None  #: str: time stamp of end of the data synchronization process

    def export_results(self, out="stdout"):
        """Routine for exporting results to either EPICS control system or printing them to STDOUT.
            Args:
                out (str): Specify output destination - valid options include "epics", "stdout"
            Returns (None):  No return
        """
        if out == "stdout":
            self.print_results()
        elif out == "epics":
            self.write_results_to_epics()
        else:
            raise ValueError("Received unsupported out value '{}'".format(out))

    def trigger_data_collection(self):
        """Method to 'force' trigger data collection.  Typically, processes should toggle between states 1 and 2
            Returns (None): No return
        """
        self.GETDATA.put(0)
        self.GETDATA.put(1)

    # TODO: finish implementing this method
    def print_results(self):
        """Routine for print results to STDOUT.  Used mostly for debug/testing"""
        fmt = "Cavity Name: {}\nCavity Type: {}\nLength: {}\nR/Q: {}\n"
        print(fmt.format(self.cavity_name, self.cavity_type, self.length, self.RQ))

    # TODO: Implement this method
    def write_results_to_epics(self):
        """Routine for writing data, metadata, and results to control system"""
        pass

    def update_formula_data(self, V_c=None, P_f=None, P_r=None, detune_angle=None, I_tot=None):
        """Updates internal formula variables, based on current PV values or optional manually supplied values

        Note: this converts PV data to base SI units, but specified values are assumed to be in SI units

        Args:
            V_c (float): Value to apply to self.V_c
            P_f (float): Value to apply to self.P_f
            P_r (float): Value to apply to self.P_r
            detune_angle (float): Value to apply to self.detune_angle (degrees)
            I_tot (float): Value to apply to self.I_tot
        Returns None:  Returns nothing
        """
        # TODO: figure out the channel access stuff
        logger.debug("Reading PV data and updating formula variables")
        # Update internal formula variables to base SI units (PVs are not necessarily in those)
        if V_c is None:
            self.V_c = self.GMESLQ.get() * self.length * 1000000
        else:
            self.V_c = V_c
        if P_f is None:
            self.P_f = self.CRFPLQ.get() * 1000
        else:
            self.P_f = P_f
        if P_r is None:
            self.P_r = self.CRRPLQ.get() * 1000
        else:
            self.P_r = P_r
        if detune_angle is None:
            self.detune_angle = math.radians(self.DETALQ.get())
        else:
            self.detune_angle = detune_angle
        if I_tot is None:
            self.I_tot = self.ITOTLQ.get() / 1000000
        else:
            self.I_tot = I_tot

    def on_GETDATA_change(self, pvname=None, value=None, char_value=None, **kw):
        """Callback function for handling changes in GETDATA PV.  Simple writes the cavity name to the 'event' queue."""
        logger.debug("on_GETDATA_change callback received %s = %s (qsize=%d)", pvname, value, self.queue.qsize())
        if value == 0:
            return
        if value == 1:
            return
        elif value == 2:
            logger.debug("on_GETDATA_change writing to queue")
            self.queue.put(self.cavity_name)

    def process_new_data(self, delay=1):
        """Method for processing new data.  Read from EPICS, run calculations, write results, and request more data.
            Args:
                delay (float): Delay is seconds from exporting results to requesting next round of data collection.
            Returns (None): Returns nothing
        """
        logger.debug("Processing new data")
        value = self.GETDATA.get()
        if value != 2:
            logger.warning("process_new_data found %s = %d (!= 2, i.e., Data Posted) (%s)", self.GETDATA.pvname, self.GETDATA.value,
                           self.cavity_name)
        self.update_formula_data()
        self.run_calculations()
        self.export_results()
        # TODO: this delay will need to move to it's own thread somewhere ... not sure about this part.
        logger.debug("About to sleep %d seconds - %s", delay, self.cavity_name)
        time.sleep(delay)
        logger.debug("Triggering next data collection")
        self.GETDATA.put(1)

    def run_calculations(self):
        """Reads current values of the synchronized *LQ PVs from the control system and performs all calculations.
            Returns (None): Returns nothing
        """
        logger.debug("Beginning calculation run")
        self.calculate_attenuation_factor()
        self.calculate_attenuation()
        self.calculate_P_fc()
        self.calculate_P_rc()
        self.calculate_Q_lf()
        self.calculate_Q_lr()
        self.data_sync_start = "now"
        self.data_sync_end = "a little later"

        # TODO: Figure out the current interface with the IOC to get timestamp info
        # self.data_sync_start = self.STARTLQ.value
        # self.data_sync_end = self.ENDLQ.value

    # # TODO: Add units to all of these attributes
    # def __init__(self, GMESLQ, CRFPLQ, CRRPLQ, DETALQ, cavity_type, length, RQ, ITOT, sync_timestamp):
    #     """Construct a cryocavity object with the specified parameters.  These parameters should
    #         Args:
    #             GMESLQ (float): measured cavity gradient in MV/m
    #             CRFPLQ (float): forward power (uncorrected) in kW
    #             CRRPLQ (float): reflected power (uncorrected) in kW
    #             DETALQ (float): relative detune angle in degrees
    #             cavity_type (str): type of cavity cell
    #             length (float): active length of cryocavity in meters
    #             RQ (float): characteristic shunt impedance in Ohms
    #             ITOT (float): beam current experienced by cavity in uA
    #             sync_timestamp (string): time stamp associated with the synchronized data collection
    #     """
    #
    #     # Constructor parameters map to the synchronized EPICS data, but the calculations all expect base SI units.
    #     # Do the unit conversion when importing the parameters
    #     self.V_c = GMESLQ * length * 1000000  #: float: cavity voltage in V
    #     self.P_f = CRFPLQ * 1000  #: float: synchronized RF forward power in W
    #     self.P_r = CRRPLQ * 1000  #: float: synchronized RF reflected power in W
    #     self.detune_angle = math.radians(
    #         DETALQ)  #: float: synchronized detune angle (called psi by F. Marhauser) in radians
    #     self.I_tot = ITOT / 1000000  #: float: Total beam current experienced by this cavity in Amps
    #
    #     # TODO: Update cavity_type to be own class?
    #     self.cavity_type = cavity_type  #: string: Type of cryocavity
    #     self.length = length  #: float: CED cryocavity length parameter for this cryocavity in meters
    #     self.RQ = RQ  #: float: cryocavity parameter (resistance / Q - called R/Q by F. Marhauser) in Ohms
    #
    #     # TODO: verify the type of the sync_timestamp parameter
    #     self.sync_timestamp = sync_timestamp  #: string: The timestamp of the FCC IOC data synchronization
    #     # TODO: verify type of calc_timestamp.  Probably should be a native date time object
    #     self.calc_timestamp = None  #: string: The timestamp when the calculations are run
    #
    #     # These attributes may/should be calculated at some point later
    #     self.attenuation_factor = None  #: float: The calculated attenuation factor.  None until calculated
    #     self.attenuation = None  #: float: The calculated attenuation.  None until calculated
    #     self.P_fc = None  #: float: The calculated corrected forward power.  None until calculated
    #     self.P_rc = None  #: float: The calculated corrected reflected power.  None until calculated
    #     self.Q_lf = None  #: float: The calculated loaded Q based on forward power.  None until calculated
    #     self.Q_lr = None  #: float: The calculated loaded Q based on reflected power.  None until calculated
    #     self.err_msg = []  #: list(string): A list of error messages that may be found during calculations

    # TODO: This should probably be moved to the main loop and only calculated twice (once for NL and SL each)
    # TODO: Keep or remove?  George has a R2XXITOT PV available
    # def calculate_beam_current(self, HA_curr, HB_curr, HC_curr, HD_curr, HA_passes, HB_passes, HC_passes, HD_passes):
    #     """Calculate the beam current experienced by a cryocavity
    #
    #         Args:
    #             HA_curr (float):  Hall A Injector current
    #             HB_curr (float):  Hall B Injector current
    #             HC_curr (float):  Hall C Injector current
    #             HD_curr (float):  Hall D Injector current
    #             HA_passes (int):  Number of passes for Hall A
    #             HD_passes (int):  Number of passes for Hall B
    #             HC_passes (int):  Number of passes for Hall C
    #             HB_passes (int):  Number of passes for Hall D
    #     """
    #     pass

    def calculate_attenuation_factor(self):
        """Calculate the attenuation factor for a cryocavity

        Note: The attenuation factor is truncate back to 0 or 1 if the calculated value is outside of [0,1].

            Returns (None): Updates the object's attenuation_factor attribute
        """

        attenuation_factor = (self.I_tot * self.V_c + math.sqrt(
            math.pow(self.I_tot * self.V_c, 2) + 4 * self.P_f * self.P_r)) / (2 * self.P_f)

        # According to F. Marhauser, this can only be in [0,1].  Truncate if bounds are exceeded.
        if attenuation_factor > 1:
            logger.warning("Attenuation factor lowered from {} to 1".format(attenuation_factor))
            self.err_msg.append("Attenuation factor lowered from {} to 1".format(attenuation_factor))
            self.attenuation_factor = 1
        elif attenuation_factor < 0:
            logger.warning("Attenuation factor raised from {} to 0".format(attenuation_factor))
            self.err_msg.append("Attenuation factor raised from {} to 0".format(attenuation_factor))
            self.attenuation_factor = 0
        else:
            self.attenuation_factor = attenuation_factor

    def calculate_attenuation(self):
        """Calculate the attenuation for a cryocavity.  Requires that the attenuation_factor has been calculated.

            Returns (None): Updates object's attenutation attribute.
        """

        self.attenuation = -10 * math.log10(self.attenuation_factor)

    def calculate_P_fc(self):
        """Compute the corrected forward power for a cryocavity.  Requires that attenuation has been calculated.

            Returns (None): Updates object's P_fc attribute.
        """

        self.P_fc = self.P_f * math.pow(10, -self.attenuation / 10)

    def calculate_P_rc(self):
        """Compute the corrected reflected power for a cryocavity.  Requires that attenuation has been calculated.

            Returns (None): Updates the object's P_rc attribute.
        """

        self.P_rc = self.P_r * math.pow(10, self.attenuation / 10)

    def calculate_Q_lf(self):
        """Calculate the loaded Q for a cryocavity using the corrected forward power.    Requires that attenuation,
         P_fc, and P_rc have been calculated.

            Returns (None): Updates the object's Q_lf attribute
        """

        self.Q_lf = ((2 * self.P_fc - self.I_tot * self.V_c - 2 * self.P_fc * math.sqrt(
            1 - (self.I_tot * self.V_c) / self.P_fc - (math.pow(self.I_tot, 2) * math.pow(self.V_c, 2)) / (
                    4 * math.pow(self.P_fc, 2)) * math.pow(math.tan(self.detune_angle), 2))) / (
                             self.RQ * math.pow(self.I_tot, 2)))

    def calculate_Q_lr(self):
        """Calculate the loaded Q for a cryocavity using the corrected reflected power

            Returns (None): Updates the object's Q_rf attribute
        """

        self.Q_lr = ((2 * self.P_rc + self.I_tot * self.V_c - 2 * self.P_rc * math.sqrt(
            1 + (self.I_tot * self.V_c) / self.P_rc - (math.pow(self.I_tot, 2) * math.pow(self.V_c, 2)) / (
                    4 * math.pow(self.P_rc, 2)) * math.pow(math.tan(self.detune_angle), 2))) / (
                             self.RQ * math.pow(self.I_tot, 2)))
