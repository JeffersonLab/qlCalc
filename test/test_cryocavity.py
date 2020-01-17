import unittest
from unittest import TestCase
from qlCalc.cryocavity import Cryocavity


class TestCryocavity(TestCase):
    c100 = Cryocavity(17.794, 3.396, 0.805, 0.67, 'c100', 0.7, 868.9, 201.8, 'some_time_2')

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


if __name__ == '__main__':
    unittest.main()
