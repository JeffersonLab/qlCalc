import math


# TODO: Add units to argument descriptions
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

    def create_cryocavity(self):
        # TODO: Implement factory constructor that accepts some generic data like beam_current, and queries EPICS and
        #  CED for other information.
        pass

    def get_synced_data(self):
        # TODO: Implement method that does the procedure for querying synchronized data from RCC IOC
        pass

    def get_ced_data(self):
        # TODO: Implement method that get CED data related to the cryocavity and it's parent cryomodule
        pass

    # TODO: Add units to all of these attributes
    def __init__(self, GMESLQ, CRFPLQ, CRRPLQ, DETALQ, cavity_type, length, RQ, ITOT, sync_timestamp):
        """Construct a cryocavity object with the specified parameters.  These parameters should
            Args:
                GMESLQ (float): measured cavity gradient in MV/m
                CRFPLQ (float): forward power (uncorrected) in kW
                CRRPLQ (float): reflected power (uncorrected) in kW
                DETALQ (float): relative detune angle in degrees
                cavity_type (str): type of cavity cell
                length (float): active length of cryocavity in meters
                RQ (float): characteristic shunt impedance in Ohms
                ITOT (float): beam current experienced by cavity in uA
                sync_timestamp (string): time stamp associated with the synchronized data collection
        """

        # Constructor parameters map to the synchronized EPICS data, but the calculations all expect base SI units.
        # Do the unit conversion when importing the parameters
        self.V_c = GMESLQ * length * 1000000  #: float: cavity voltage in V
        self.P_f = CRFPLQ * 1000  #: float: synchronized RF forward power in W
        self.P_r = CRRPLQ * 1000  #: float: synchronized RF reflected power in W
        self.detune_angle = math.radians(
            DETALQ)  #: float: synchronized detune angle (called psi by F. Marhauser) in radians
        self.I_tot = ITOT / 1000000  #: float: Total beam current experienced by this cavity in Amps

        # TODO: Update cavity_type to be own class?
        self.cavity_type = cavity_type  #: string: Type of cryocavity
        self.length = length  #: float: CED cryocavity length parameter for this cryocavity in meters
        self.RQ = RQ  #: float: cryocavity parameter (resistance / Q - called R/Q by F. Marhauser) in Ohms

        # TODO: verify the type of the sync_timestamp parameter
        self.sync_timestamp = sync_timestamp  #: string: The timestamp of the FCC IOC data synchronization
        # TODO: verify type of calc_timestamp.  Probably should be a native date time object
        self.calc_timestamp = None  #: string: The timestamp when the calculations are run

        # These attributes may/should be calculated at some point later
        self.attenuation_factor = None  #: float: The calculated attenuation factor.  None until calculated
        self.attenuation = None  #: float: The calculated attenuation.  None until calculated
        self.P_fc = None  #: float: The calculated corrected forward power.  None until calculated
        self.P_rc = None  #: float: The calculated corrected reflected power.  None until calculated
        self.Q_lf = None  #: float: The calculated loaded Q based on forward power.  None until calculated
        self.Q_lr = None  #: float: The calculated loaded Q based on reflected power.  None until calculated
        self.err_msg = []  #: list(string): A list of error messages that may be found during calculations

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
            self.err_msg.append("Attenuation factor lowered from {} to 1".format(attenuation_factor))
            self.attenuation_factor = 1
        elif attenuation_factor < 0:
            self.err_msg.append("Attenuation factor raised from {} to 0".format(attenuation_factor))
            self.attenuation_factor = 0
        else:
            self.attenuation_factor = attenuation_factor

    def calculate_attenuation(self):
        """Calculate the attenuation for a cryocavity

            Returns (None): Updates object's attenutation attribute.
        """

        self.attenuation = -10 * math.log10(self.attenuation_factor)

    def calculate_P_fc(self):
        """Compute the corrected forward power for a cryocavity

            Returns (None): Updates object's P_fc attribute.
        """

        self.P_fc = self.P_f * math.pow(10, -self.attenuation / 10)

    def calculate_P_rc(self):
        """Compute the corrected reflected power for a cryocavity

            Returns (None): Updates the object's P_rc attribute.
        """

        self.P_rc = self.P_r * math.pow(10, self.attenuation / 10)

    def calculate_Q_lf(self):
        """Calculate the loaded Q for a cryocavity using the corrected forward power

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
