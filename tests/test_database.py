import unittest
import impact as impt
import os
import pandas as pd

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.session = impt.database.create_session()
        engine = impt.database.bind_engine()
        impt.database.Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        try:
            os.remove('default_impt.db')
        except FileNotFoundError:
            pass

    def test_trial_identifier(self):
        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                           for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]
        for component in components:
            LIMS.add_component(component)
        ti = impt.ReplicateTrialIdentifier(strain=impt.Strain(name='MG1655 WT'))
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()
        del ti
        del strain
        ti = self.session.query(impt.ReplicateTrialIdentifier).one()

        self.assertEqual(ti.strain.name, 'test strain')
        self.trial_identifier = ti

    def test_time_course(self):
        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                           for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]
        for component in components:
            LIMS.add_component(component)

        ti = impt.TimeCourseIdentifier(strain=impt.Strain(name='MG1655 WT'))
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()
        ti = self.session.query(impt.TimeCourseIdentifier).all()[0]

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        for time, data in ((0, 0), (1, 5), (2, 10)):
            tc.add_timepoint(impt.TimePoint(trial_identifier=ti, time=time, data=data))
        tc.pd_series = pd.Series([timePoint.data for timePoint in tc.time_points],index=[timePoint.time for timePoint in\
                                                                                         tc.time_points])
        self.session.add(tc)
        self.session.commit()

        del tc
        tc = self.session.query(impt.TimeCourse).all()[0]
        tc.calculate()

        self.assertCountEqual(tc.data_vector,[0,5,10])
        self.assertCountEqual(tc.time_vector,[0,1,2])

    def test_single_trial(self):
        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                           for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]
        for component in components:
            LIMS.add_component(component)

        ti = impt.TimeCourseIdentifier(strain=impt.Strain(name='MG1655 WT'))
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()

        ti = self.session.query(impt.TimeCourseIdentifier).all()[0]

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        for time, data in ((0, 0), (1, 5), (2, 10)):
            tc.add_timepoint(impt.TimePoint(trial_identifier=ti, time=time, data=data))
        tc.pd_series = pd.Series([timePoint.data for timePoint in tc.time_points],index=[timePoint.time for timePoint in\
                                                                                         tc.time_points])

        self.session.add(tc)

        st = impt.SingleTrial()
        st.add_analyte_data(tc)

        rep = impt.ReplicateTrial()
        rep.add_replicate(st)

        expt = impt.Experiment()
        expt.add_replicate_trial(rep)

        self.session.add(expt)
        self.session.commit()
        del expt

        expt = self.session.query(impt.Experiment).all()[0]
        tc = [time_course
               for replicate in expt.replicate_trial_dict.values()
               for single_trial in replicate.single_trial_dict.values()
               for time_course in single_trial.analyte_dict.values()
                ][0]
        self.assertCountEqual(tc.data_vector,[0,5,10])
        self.assertCountEqual(tc.time_vector,[0,1,2])

if __name__ == 'main':
    unittest.main()