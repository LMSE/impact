import unittest
import impact
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class TestStages(unittest.TestCase):
    def test_stage_parsing(self):
        expt = impact.Experiment()
        expt.parse_raw_data('default_titers',
                            file_name=os.path.join(BASE_DIR, 'tests/test_data/sample_input_data.xlsx'))
        expt.set_stages(stage_indices=[[0,6],[6,15]])

        expt.calculate()

        # expt.calculate()
        for stage in expt.stages.values():
            # print('in1')
            for replicate in stage.replicate_trial_dict.values():
                # print('in2')
                for single_trial in replicate.single_trial_dict.values():
                    # print('in3')
                    for analyte in single_trial.analyte_dict.values():
                        # print('in4')
                        # print(min(analyte.time_vector))
                        # print(max(analyte.time_vector))
                        self.assertGreaterEqual(min(analyte.time_vector),stage.start_time)
                        self.assertLessEqual(max(analyte.time_vector),stage.end_time)
