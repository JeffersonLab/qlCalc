import unittest
from unittest import TestCase
from qlCalc.cryocavity import Cryocavity
import time
import math
import threading


class TestCryocavity(TestCase):
    c100 = Cryocavity(GETDATA=None, GMESLQ=None, CRFPLQ=None, CRRPLQ=None, DETALQ=None, ITOTLQ=None, STARTLQ=None,
                      ENDLQ=None, cavity_name="my_cav", cavity_type="my_cav_type", length=0.7, RQ=868.9,
                      update_queue=None, request_interval=1, shutdown_event=threading.Event())
    c100.update_formula_data(V_c=(17.794 * 0.7 * 1000000), P_f=(3.396 * 1000), P_r=(0.805 * 1000),
                             detune_angle=math.radians(0.67), I_tot=(201.8 / 1000000))

    # GMESLQ, CRFPLQ, CRRPLQ, DETALQ, cavity_type, length, RQ, ITOT, sync_timestamp
    # c100 = Cryocavity(17.794, 3.396, 0.805, 0.67, 'c100', 0.7, 868.9, 201.8, 'some_time_2')

    def test_1_calculate_attenuation_factor(self):
        self.c100.calculate_attenuation_factor()
        res = self.c100.attenuation_factor
        exp = 0.981636983
        self.assertAlmostEqual(exp, res, 6)

        # TODO: Add additional cases, one for each cell type at least?
        # Example from Frank's old, large spreadsheet - only same out to three decimals
        # cc = Cryocavity(7.848, 2.55, 0.42, -9.2, 'c25', 0.5, 482.5, 426, 'some_time')
        # cc.calculate_attenuation_factor()
        # res = cc.attenuation_factor
        # exp = 0.849626464
        # self.assertAlmostEqual(exp, res, 6)

    def test_2_calculate_attenuation(self):
        self.c100.calculate_attenuation()
        exp = 0.080490882
        res = self.c100.attenuation
        self.assertAlmostEqual(exp, res, 6)

    def test_3_calculate_P_fc(self):
        self.c100.calculate_P_fc()
        exp = 3333.6391931051
        res = self.c100.P_fc
        self.assertAlmostEqual(exp, res, 6)

    def test_calculate_P_rc(self):
        self.c100.calculate_P_rc()
        exp = 820.0587531051
        res = self.c100.P_rc
        self.assertAlmostEqual(exp, res, 6)

    def test_calculate_Q_lf(self):
        self.c100.calculate_Q_lf()
        exp = 23937066.5884476000000
        res = self.c100.Q_lf
        self.assertAlmostEqual(exp, res, 6)

    def test_calculate_Q_lr(self):
        self.c100.calculate_Q_lr()
        exp = 23937066.5884476000000
        res = self.c100.Q_lf
        self.assertAlmostEqual(exp, res, 6)

    def test_calculation_performance_is_acceptable(self):
        start = time.perf_counter()
        n = 408
        for x in range(0, n):
            self.c100.run_calculations()
        end = time.perf_counter()
        print("{} calculations took {} seconds".format(n, end - start))
        self.assertGreater(0.1, end-start)


if __name__ == '__main__':
    unittest.main()
