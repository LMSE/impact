import unittest
import impact as impt
import os
import pandas as pd


class TestExperiment(unittest.TestCase):
    def test_add_experiment(self):
        impt.settings.savgolFilterWindowSize = 9
        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                           for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]
        for component in components:
            LIMS.add_component(component)
        ti1 = impt.TimeCourseIdentifier(strain=impt.Strain(name='MG1655 WT'))
        ti1.media = LIMS
        ti1.analyte_type = 'biomass'
        ti1.analyte_name = 'OD600'
        strain1 = impt.Strain(name='test strain1')
        ti1.strain = strain1
        tc1 = impt.Biomass()
        tc1.trial_identifier = ti1
        for time, data in ((0, 0.05),
                           (1, 0.06),
                           (2, 0.08),
                           (3, 0.1),
                           (4, 0.2),
                           (5, 0.4),
                           (6, 0.8),
                           (7, 1.6),
                           (8, 1.6),
                           (9, 1.6),
                           (10, 1.6)):
            tc1.add_timepoint(impt.TimePoint(trial_identifier=ti1, time=time, data=data))
        tc1.pd_series = pd.Series([timePoint.data for timePoint in tc1.time_points],index=[timePoint.time for timePoint in\
                                                                                         tc1.time_points])
        st1 = impt.SingleTrial()
        st1.add_analyte_data(tc1)
        rep1 = impt.ReplicateTrial()
        rep1.add_replicate(st1)
        expt1 = impt.Experiment()
        expt1.add_replicate_trial(rep1)


        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                      for name, concentration, unit in [
                          ['cAA', 0.02, '%'],
                          ['IPTG', 1, 'M']
                      ]]
        for component in components:
            LIMS.add_component(component)

        ti2 = impt.TimeCourseIdentifier(strain=impt.Strain(name='blank'))
        ti2.media = LIMS
        ti2.analyte_type = 'biomass'
        ti2.analyte_name = 'OD600'
        strain2 = impt.Strain(name='blank')
        ti2.strain = strain2

        tc2 = impt.Biomass()
        tc2.trial_identifier = ti2
        for time, data in ((0, 0.05), (1, 0.05), (2, 0.05),
                           (3, 0.05), (4, 0.05), (5, 0.05),
                           (6, 0.05), (7, 0.05), (8, 0.05),
                           (9, 0.05), (10, 0.05)):
            tc2.add_timepoint(impt.TimePoint(trial_identifier=ti2, time=time, data=data))
        tc2.pd_series = pd.Series([timePoint.data for timePoint in tc2.time_points],
                                 index=[timePoint.time for timePoint in \
                                        tc2.time_points])

        st2 = impt.SingleTrial()
        st2.add_analyte_data(tc2)

        rep2 = impt.ReplicateTrial()
        rep2.add_replicate(st2)

        expt2 = impt.Experiment()
        expt2.add_replicate_trial(rep2)

        expt = expt1 + expt2

        expt1.set_stages([(0,2)])
        expt2.set_stages([(0,2)])

        expt1.calculate()
        expt2.calculate()

        self.assertCountEqual(expt.strains,['test strain1', 'blank'])
        self.assertCountEqual(expt.analyte_names,['OD600'])
        stage_tc1 = expt1.stages['0-2'].replicate_trials[0].single_trials[0].analyte_dict['OD600']
        self.assertEqual(len(stage_tc1.data_vector),2)
        self.assertEqual(len(stage_tc1.time_vector),2)
        stage_tc2 = expt2.stages['0-2'].replicate_trials[0].single_trials[0].analyte_dict['OD600']
        self.assertEqual(len(stage_tc2.data_vector),2)
        self.assertEqual(len(stage_tc2.time_vector), 2)
        print("Printing test expt.....")
        print(expt)
        self.assertEqual(len(expt1.data()), 6)



        expt.calculate()

        pass