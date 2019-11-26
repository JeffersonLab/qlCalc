import math

# TODO: Add units to argument descriptions

class Cryocavity(object):
    """A class representing a CEBAF Cryocavity.
    
    This class contains all logic required for calculating its loaded values, including
    querying the control system and other services for data, running calculations, and 
    writing data back to the control system.

    This class contains both a factory method and regular constructor.  Factory method
    should be used in general, but the regular constructor is convenient for test cases.
    """

    def factory():
        # TODO: Implement factory constructor that accepts some generic data like beam_current, and queries EPICS and CED for other infomration.
        pass

    def get_synched_data():
        # TODO: Implment method that does the procedure for querying synchronized data from RCC IOC
        pass

    def get_CED_data():
        # TODO: Implement method that get CED data related to the cryocavity and it's parent cryomodule
        pass

    # TODO: Add units to all of these attributes
    def __init__(self,V_c, P_f, P_r, detune_angle, cm_type, length, RQ, beam_current, synch_timestamp):
        """Construct a cryocavity object with the specified parameters.
        """

        self.V_c = V_c #: float: cavity voltage, i.e. GMESLQ * cavity length
        self.P_f = P_f #: float: synchronized RF forward power
        self.P_r = P_r #: float: synchronized RF reflected power

        # TODO: validate this PV name for detune_angle
        self.detune_angle  #: float: synchronized detune angle (called psi by F. Marhuaser)
        self.cm_type = cm_type #: string: CED cmType for parent cryomodule
        self.length = length #: float: CED cryocavity length parameter for this cryocavity

        # TODO: talk with Frank about this RQ parameter
        self.RQ = RQ #: float: cryocavity parameter (resistance / Q - called R/Q by F. Marhauser)
        self.beam_current = beam_current #: float: Total beam current experienced by this cavity

        # TODO: verify the type of the parameter
        self.sync_timestamp = sync_timestamp #: string: The timestamp of the FCC IOC data synchronization

        # These attributes may/should be calculated at some point later
        self.attenuation_factor = None   #: float: The calculated attenuation factor.  None until calculated
        self.attenuation = None          #: float: The calculated attenuation.  None until calculated
        self.P_fc = None                 #: float: The calculated corrected forward power.  None until calculated
        self.P_rc = None                 #: float: The calculated corrected reflected power.  None until calculated
        self.Q_lf = None                 #: float: The calculated loaded Q based on forward power.  None until calculated
        self.Q_lr = None                 #: float: The calculated loaded Q based on reflected power.  None until calculated

    # TODO: This should probably be moved to the main loop and only calculated twice (once for NL and SL each)
    def calculate_I_tot(HA_curr, HB_curr, HC_curr, HD_curr, HA_passes, HB_passes, HC_passes, HD_passes):
        """Calculate the beam current experienced by a cryocavity

            Args:
                HA_curr (float):  Hall A Injector current
                HB_curr (float):  Hall B Injector current
                HC_curr (float):  Hall C Injector current
                HD_curr (float):  Hall D Injector current
                HA_passes (int):  Number of passes for Hall A
        """
        pass

    def calculate_attenuation_factor():
        """Caclulate the attenuation factor for a cryocavity

        Note: The attenuation factor is truncate back to 0 or 1 if the calculated value is outside of [0,1].

            Returns (None): Updates the object's attenuation_factor attribute
        """

        attentuation_factor = (I_tot*V_c _ math.sqrt((I_tot*V_c)**2 + 4*P_f*P_r)) / (2*P_f)

        # According to F. Marhauser, this can only be in [0,1].  Truncate if bounds are exceeded.
        if attentuation_factor > 1:
            attentuation_factor = 1
        elif attenuation_factor < 0:
            attenuation_factor = 0
            
        return attentuation_factor

    def calculate_attenuation ():
        """Calculate the attenuation for a cryocavity

            Returns (None): Updates object's attenutation attribute.
        """

        return (-10 * math.log10(attenuation_factor))

    def calculate_P_fc():
        """Compute the corrected forward power for a cryocavity

            Returns (None): Updates object's P_fc attribute.
        """

        P_fc = P_f * math.pow(10, -attentuation/10)

    def calculate_P_rc():
        """Compute the corrected reflected power for a cryocavity

            Returns (None): Updates the object's P_rc attribute.
        """

        P_rc = P_r * math.pow(10, attentuation/10)

    def calculate_Q_lf():
        """Calculate the loaded Q for a cryocavity using the corrected forward power

            Returns (None): Updates the object's Q_lf attribute
        """

        Q_lf = ((2*P_fc - I_tot*V_c - 2*P_fc * math.sqrt(1 - (I_tot*V_c)/P_fc - (math.pow(I_tot, 2) * math.pow(V_c, 2))/(4*math.pow(P_fc,2)) * math.pow(math.tan(detune_angle), 2)) ) 
                    / (RQ * math.pow(I_tot, 2)))


    def calculate_Q_lr():
        """Calculate the loaded Q for a cryocavity using the corrected reflected power

            Returns (None): Updates the object's Q_rf attribute
        """

        Q_rf = ((2*P_rc + I_tot*V_c - 2*P_rc * math.sqrt(1 + (I_tot*V_c)/P_rc - (math.pow(I_tot, 2) * math.pow(V_c, 2))/(4*math.pow(P_rc,2)) * math.pow(math.tan(detune_angle), 2)) ) 
                    / (RQ * math.pow(I_tot, 2)))
