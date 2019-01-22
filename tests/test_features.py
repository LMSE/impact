import unittest
import impact as impt
import numpy as np
from impact.core.AnalyteData import Biomass, Reporter
from impact.core.SingleTrial import SingleTrial
from impact.core.TrialIdentifier import ReplicateTrialIdentifier as TrialIdentifier

class TestFeatures(unittest.TestCase):
    def test_specific_productivity(self):
        ti = impt.ReplicateTrialIdentifier()
        ti.analyte_name = 'OD600'
        ti.analyte_type = 'biomass'

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        tc.time_vector = [0,1,2,3,4,5]
        tc.data_vector = [0.05,0.1,0.2,0.4,0.8,1.6]

        st = impt.SingleTrial()
        st.add_analyte_data(tc)

        ti = impt.ReplicateTrialIdentifier()
        ti.analyte_name = 'etoh'
        ti.analyte_type = 'product'

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        tc.time_vector = [0, 1, 2, 3, 4, 5]
        tc.data_vector = [1, 2, 3, 4, 5, 6]

        st.add_analyte_data(tc)

        self.assertCountEqual(st.analyte_dict['etoh'].specific_productivity.data,
                         np.array([20.,10.,5.,2.5,1.25,0.625]))

    def test_od_normalization(self):
        t = [0, 1, 2, 3, 4]
        biomass_data = [0.1, 0.2, 0.4, 0.8, 0.8]
        reporter_data = [1000, 2000, 3000, 4000, 5000]

        biomass = Biomass()
        biomass.time_vector = t
        biomass.data_vector = biomass_data
        ti = TrialIdentifier()
        ti.analyte_name = 'OD'
        ti.analyte_type = 'biomass'
        biomass.trial_identifier = ti

        reporter = Reporter()
        reporter.time_vector = t
        reporter.data_vector = reporter_data
        ti = TrialIdentifier()
        ti.analyte_name = 'gfp'
        ti.analyte_type = 'reporter'
        reporter.trial_identifier = ti

        trial = SingleTrial()
        trial.add_analyte_data(biomass)
        trial.add_analyte_data(reporter)

        calculated_data = trial.analyte_dict['gfp'].od_normalized_data.data
        expected_data = np.array(reporter_data) / biomass_data

        self.assertListEqual(expected_data.tolist(),calculated_data.tolist())

if __name__ == '__main__':
    unittest.main()