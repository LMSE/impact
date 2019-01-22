import unittest
import impact
import os
import impact.parsers as parsers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class TestParsers(unittest.TestCase):

    def test_generic_identifier_parser(self):
        ti = impact.ReplicateTrialIdentifier()
        ti.parse_identifier(
            'time:1|'
            'environment__labware:Falcon96|'
            'environment__shaking_speed:250|'
            'environment__temperature:37|'
            'media__base:LIMS|'
            'media__cc:10 glc__D|'
            'rep:1|'
            'strain__id:D1|'
            'strain__ko:adh,pta,lacI|'
            'strain:MG|'
            'strain__plasmid:pKDL|'
            'strain__plasmid:pKDL3|'
            'strain__plasmid:pKDL2')
        self.assertEqual(ti.time,1.)
        self.assertEqual(ti.environment.labware.name,'Falcon96')
        self.assertEqual(ti.environment.shaking_speed,250)
        self.assertEqual(ti.environment.temperature,37)
        self.assertEqual(ti.media.parent,'LIMS')
        print(ti.media.components)
        self.assertEqual(ti.media.components['glc__D'].component_name,'glc__D')
        self.assertEqual(ti.media.components['glc__D'].concentration,10)
        self.assertEqual(ti.replicate_id,1)
        # self.assertEqual(ti.strain.id,'D1') #TODO update
        self.assertEqual(ti.strain.name,'MG')
        self.assertIn('pKDL',[plasmid.name for plasmid in ti.strain.plasmids])
        self.assertIn('pKDL2',[plasmid.name for plasmid in ti.strain.plasmids])
        self.assertIn('pKDL3',[plasmid.name for plasmid in ti.strain.plasmids])


    def test_default_HPLC_parser(self):
        expt = impact.Experiment()
        parsers.Parser.parse_raw_data(data_format='default_titers', file_name=os.path.join(BASE_DIR, 'tests/test_data/sample_input_data.xlsx'), experiment=expt, id_type='CSV')

        num_replicates = (len(expt.replicate_trial_dict.keys()))

        num_single_trials = len([
            single_trial_key for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
        ])

        num_analyte_data = len([
            analyte_name for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
        ])

        num_time_points = len([
            time_point for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
            for time_point in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict[analyte_name].time_points
        ])

        self.assertEqual(num_replicates,7)
        self.assertEqual(num_single_trials,18)
        self.assertEqual(num_analyte_data,252)
        self.assertEqual(num_time_points,2884)

    def test_spectromax_parser(self):
        expt = impact.Experiment()
        parsers.Parser.parse_raw_data(data_format='spectromax_OD', id_type='traverse', file_name=os.path.join(BASE_DIR,'tests/test_data/sample_spectromax_data.xlsx'), experiment = expt)

        num_replicates = (len(expt.replicate_trial_dict.keys()))

        num_single_trials = len([
            single_trial_key for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
        ])

        num_analyte_data = len([
            analyte_name for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
        ])

        num_time_points = len([
            time_point for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
            for time_point in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict[analyte_name].time_points
        ])

        self.assertEqual(num_replicates,32)
        self.assertEqual(num_single_trials,88)
        self.assertEqual(num_analyte_data,88)
        self.assertEqual(num_time_points,880)


    def test_tecan_OD_parser(self):
        expt = impact.Experiment()
        parsers.Parser.parse_raw_data(data_format='tecan', id_type='traverse', file_name=os.path.join(BASE_DIR,'tests/test_data/sample_tecan_OD_data.xlsx'), experiment=expt)

        num_replicates = (len(expt.replicate_trial_dict.keys()))

        num_single_trials = len([
            single_trial_key for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
        ])

        num_analyte_data = len([
            analyte_name for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
        ])

        num_time_points = len([
            time_point for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
            for time_point in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict[analyte_name].time_points
        ])

        self.assertEqual(num_replicates,56)
        self.assertEqual(num_single_trials,96)
        self.assertEqual(num_analyte_data,96)
        self.assertEqual(num_time_points,960)

    def test_tecan_OD_reporter_parser(self):
        expt = impact.Experiment()
        parsers.Parser.parse_raw_data(data_format='tecan', id_type='traverse',
                                      file_name=os.path.join(BASE_DIR,
                                                             'tests/test_data/sample_tecan_OD_reporter_data.xlsx'),
                                      experiment=expt)

        num_replicates = (len(expt.replicate_trial_dict.keys()))

        num_single_trials = len([
            single_trial_key for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
        ])

        num_analyte_data = len([
            analyte_name for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in
            expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
        ])

        num_time_points = len([
            time_point for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in
            expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
            for time_point in
            expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict[
                analyte_name].time_points
        ])

        self.assertEqual(num_replicates, 56)
        self.assertEqual(num_single_trials, 96)
        self.assertEqual(num_analyte_data, 288)
        self.assertEqual(num_time_points, 2880)


if __name__ == '__main__':
    unittest.main()