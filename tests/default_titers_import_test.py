import impact
import datetime
import unittest
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        # info = {
        #     'importDate': datetime.datetime.today(),
        #     'runStartDate': datetime.datetime.today(),
        #     'runEndDate':datetime.datetime.today(),
        #     'principalScientistName':'impact Test',
        #     'mediumBase':'NA',
        #     'mediumSupplements':'NA',
        #     'notes':'This is a test of the default_titers parser',
        #     'experimentTitle': 'default_titer test'
        # }
        # self.db_name = 'test_impact_db.sqlite3'
        # try:
        #     os.remove('test_impact.db')
        # except FileNotFoundError:
        #     pass
        #
        engine = impact.database.bind_engine()
        impact.database.Base.metadata.create_all(engine)
        # Create experiment
        self.expt = impact.Experiment()
        self.session = impact.create_session()
        # session.add(expt)
        # session.commit()
        # session.close()
        # Init a temp db
        # impact.init_db(db_name=self.db_name)

    def tearDown(self):
        # Delete the temp db
        # pass
        self.session.close()
        # import os
        # os.remove(self.db_name)

    def test_default_titers_parse(self):
        # Parse the data
        self.expt.parse_raw_data('default_titers', file_name=os.path.join(BASE_DIR, 'tests/test_data/sample_input_data.xlsx'))

        # Commit to the db
        # experiment_id = self.expt.db_commit(db_name=self.db_name)

        # Reinstantiate and import from db
        # expt = impact.Experiment()
        # expt.db_load(db_name = self.db_name, experiment_id = experiment_id)
        self.session.add(self.expt)
        self.session.commit()
        id = self.expt.id
        expt = self.session.query(impact.Experiment).get(id)
        # Plot
        expt.printGenericTimeCourse(titersToPlot=['pyruvate', 'acetate', '1,3-butanediol', 'acetaldehyde',
                                                  'ethanol', 'meso-2,3-butanediol', 'acetoin'],
                                    output_type='image')

    def test_default_titers_missing_data(self):
        """
        Test importing data with missing data
        """
        # Parse the data
        self.expt.parse_raw_data('default_titers', file_name='test_data/sample_input_data_missing_data.xlsx')

        # Commit to the db
        # experiment_id = self.expt.db_commit(db_name=self.db_name)

        # Reinstantiate and import from db
        # expt = impact.Experiment()
        # expt.db_load(db_name=self.db_name, experiment_id=experiment_id)

        # Plot
        # self.expt.printGenericTimeCourse(titersToPlot=['pyruvate', 'acetate', '1,3-butanediol', 'acetaldehyde',
        #                                           'ethanol', 'meso-2,3-butanediol', 'acetoin'],
        #                             output_type='image', titerFlag = False, yieldFlag = True)

class BasicTestCase(unittest.TestCase):
    def test_create_trial_identifier(self):
        pass

    def test_create_analyte_data(self):
        pass



if __name__ == '__main__':
    unittest.main()