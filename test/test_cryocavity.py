from unittest import TestCase
from qlCalc.cryocavity import Cryocavity


class TestCryocavity(TestCase):
    def test_calculate_attenuation_factor(self):

        cc = Cryocavity(17.794, 3.396, 0.805, 0.67, 'c100', 0.7, 868.9, 201.8, 'some_time_2')
        cc.calculate_attenuation_factor()
        res = cc.attenuation_factor
        exp = 0.981636983
        self.assertAlmostEqual(exp, res, 6)

        # TODO: Add additional cases, one for each cell type at least?
        # Example from Frank's old, large spreadsheet - only same out to three decimals
        # cc = Cryocavity(7.848, 2.55, 0.42, -9.2, 'c25', 0.5, 482.5, 426, 'some_time')
        # cc.calculate_attenuation_factor()
        # res = cc.attenuation_factor
        # exp = 0.849626464
        # self.assertAlmostEqual(exp, res, 6)
