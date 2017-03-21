import copy
import datetime
import time
import time as sys_time
from collections import OrderedDict

import numpy as np
from pyexcel_xlsx import get_data

from .core.AnalyteData import TimePoint
from .core.TrialIdentifier import TrialIdentifier, Strain


# "strain_ko=adh,pta;strain_gen1=D1;plasmid_name=pKDL071;inducer=IPTG"
#
# 'var_val_delim ='
# 'id_delim ;'


def generic_id_parser(self, id, id_val_delim='=', id_delim=';'):
    assert isinstance(id,str)

    pairs = id.split(id_delim)
    id_val = {pair.split(id_val_delim)[0] : pair.split(id_val_delim)[1] for pair in pairs}

    strain = Strain()
    if 'strain_ko' in id_val.keys():
        strain.knockouts = id_val['strain_ko']



    return id_val

def spectromax_OD(experiment, data, fileName = None):
    from .core.settings import settings
    live_calculations = settings.live_calculations
    
    # This should be an ordered dict if imported from py_xlsx
    assert isinstance(data, OrderedDict)


    identifiers = data['identifiers']
    raw_data = data['data']

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []

    for start_row_index in range(3, len(raw_data), 9):
        # print(start_row_index)
        # Parse the time point out first
        # print(raw_data[start_row_index][0])

        if raw_data[start_row_index][0] != '~End':
            if isinstance(raw_data[start_row_index][0],datetime.datetime):
                raise Exception("Imported a datetime object, make sure to set all cells to 'TEXT' if importing"
                                " from excel")
            parsed_time = raw_data[start_row_index][0].split(':')

            # Convert the Spectromax format to raw hours
            if len(parsed_time) > 2:
                time = int(parsed_time[0]) * 3600 + int(parsed_time[1]) * 60 + int(parsed_time[2])
            else:
                time = int(parsed_time[0]) * 60 + int(parsed_time[1])

            time /= 3600  # convert to hours

            # Define the data for a single plate, single timepoint
            plate_data = [row[2:14] for row in raw_data[start_row_index:start_row_index+8]]
            # print(plate_data)

            # Load the data point by point
            for i, row in enumerate(plate_data):
                for j, data in enumerate(row):
                    # Skip wells where no identifier is listed or no data present
                    if identifiers[i][j] != '' and data != '':
                        temp_trial_identifier = TrialIdentifier()
                        temp_trial_identifier.parse_trial_identifier_from_csv(identifiers[i][j])
                        temp_trial_identifier.analyte_type = 'biomass'
                        temp_trial_identifier.analyte_name = 'OD600'
                        try:
                            # print('gooddata:', data)
                            temp_timepoint = TimePoint(temp_trial_identifier, time, float(data))
                        except Exception as e:
                            # print('baddata:',data)
                            print(plate_data)
                            raise Exception(e)
                        timepoint_list.append(temp_timepoint)
                    # else:
                    #     print('Skipped time point')
        else:
            break

    experiment.parse_time_point_dict(timepoint_list)

    if live_calculations:   experiment.calculate()


def spectromax_OD_triplicate(experiment, data, fileName=None):
    from .core.settings import settings
    live_calculations = settings.live_calculations

    # This should be an ordered dict if imported from py_xlsx
    assert isinstance(data, OrderedDict)

    identifiers = data['identifiers']
    raw_data = data['data']

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []

    for start_row_index in range(3, len(raw_data), 9):
        # print(start_row_index)
        # Parse the time point out first
        # print(raw_data[start_row_index][0])

        if raw_data[start_row_index][0] != '~End':
            if isinstance(raw_data[start_row_index][0], datetime.datetime):
                raise Exception("Imported a datetime object, make sure to set all cells to 'TEXT' if importing"
                                " from excel")
            parsed_time = raw_data[start_row_index][0].split(':')

            # Convert the Spectromax format to raw hours
            if len(parsed_time) > 2:
                time = int(parsed_time[0]) * 3600 + int(parsed_time[1]) * 60 + int(parsed_time[2])
            else:
                time = int(parsed_time[0]) * 60 + int(parsed_time[1])

            time /= 3600  # convert to hours

            # Define the data for each of the replicates
            replicate_plate_data = [[row[2:14] for row in raw_data[start_row_index:start_row_index + 8]],
                                    [row[15:27] for row in raw_data[start_row_index:start_row_index + 8]],
                                    [row[28:40] for row in raw_data[start_row_index:start_row_index + 8]]]

            # convert to strings to floats
            converted_data = []
            for plate_data in replicate_plate_data:
                converted_data.append([[float(data) for data in row] for row in plate_data])


            # from pprint import pprint
            # print(replicate_plate_data)

            # Calculate the average
            plate_data = np.mean(converted_data,axis=0)

            # Load the data point by point
            for i, row in enumerate(plate_data):
                for j, data in enumerate(row):
                    # Skip wells where no identifier is listed or no data present
                    if identifiers[i][j] != '' and data != '':
                        temp_trial_identifier = TrialIdentifier()
                        temp_trial_identifier.parse_trial_identifier_from_csv(identifiers[i][j])
                        temp_trial_identifier.analyte_type = 'biomass'
                        temp_trial_identifier.analyte_name = 'OD600'
                        temp_timepoint = TimePoint(temp_trial_identifier, time, float(data))

                        timepoint_list.append(temp_timepoint)
                        # else:
                        #     print('Skipped time point')
        else:
            break

    experiment.parse_time_point_dict(timepoint_list)

    if live_calculations:   experiment.calculate()


def HPLC_titer_parser(experiment, data, fileName):
    t0 = sys_time.time()

    # Parameters
    row_with_titer_names = 0
    row_with_titer_types = 1
    first_data_row = 2
    titerDataSheetName = "titers"
    if fileName is not None:
        from collections import OrderedDict
        if type(data) in [dict, type(OrderedDict())]:
            if 'titers' not in data.keys():  # TODO data has no keys if there is only one sheet
                raise Exception("No sheet named 'titers' found")
        else:
            data = {titerDataSheetName: data}
    elif data is not None:
        data = {titerDataSheetName: data}
    else:
        raise Exception('No fileName or data')

    # Initialize variables
    analyte_nameColumn = dict()
    titer_type = dict()
    for i in range(1, len(data[titerDataSheetName][row_with_titer_names])):
        analyte_nameColumn[data[titerDataSheetName][row_with_titer_names][i]] = i
        titer_type[data[titerDataSheetName][row_with_titer_names][i]] = \
            data[titerDataSheetName][row_with_titer_types][i]

    # Initialize a timepoint_collection for each titer type (column)
    tempTimePointCollection = dict()
    for names in analyte_nameColumn:
        tempTimePointCollection[names] = []
    skipped_lines = 0
    timepoint_list = []
    for i in range(first_data_row, len(data['titers'])):
        if type(data['titers'][i][0]) is str:


            # temp_run_identifier_object.strain.name = strain_rename_dict[temp_run_identifier_object.strain.name]

            for key in tempTimePointCollection:
                trial_identifier = TrialIdentifier()
                trial_identifier.parse_trial_identifier_from_csv(data['titers'][i][0])
                trial_identifier.analyte_name = key
                trial_identifier.analyte_type = titer_type[key]
                # if key == substrate_name:
                #     temp_run_identifier_object.titerType = 'substrate'
                # else:
                #     temp_run_identifier_object.titerType = 'product'

                # Remove these time points
                # if temp_run_identifier_object.time not in [12, 72, 84]:
                # print(temp_run_identifier_object.time,' ',data['titers'][i][analyte_nameColumn[key]])
                if data['titers'][i][analyte_nameColumn[key]] == 'nan':
                    data['titers'][i][analyte_nameColumn[key]] = np.nan
                timepoint_list.append(
                    TimePoint(trial_identifier,
                              trial_identifier.time,
                              data['titers'][i][analyte_nameColumn[key]]))

        else:
            skipped_lines += 1
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(timepoint_list), tf - t0))
    print("Number of lines skipped: ", skipped_lines)
    experiment.parse_time_point_dict(timepoint_list)
    experiment.calculate()

def tecan_OD(experiment, data, fileName, t0):
    from .core.AnalyteData import TimeCourse

    t0 = sys_time.time()
    if fileName:
        # Check for correct data for import
        if 'OD' not in data.keys():
            raise Exception("No sheet named 'OD' found")
        else:
            ODDataSheetName = 'OD'

        data = data[ODDataSheetName]

    # Parse data into timeCourseObjects
    skipped_lines = 0
    timeCourseObjectList = dict()
    for row in data[1:]:
        temp_run_identifier_object = TrialIdentifier()
        if type(row[0]) is str:
            temp_run_identifier_object.parse_trial_identifier_from_csv(row[0])
            temp_run_identifier_object.analyte_name = 'OD600'
            temp_run_identifier_object.analyte_type = 'biomass'
            temp_time_course = TimeCourse()
            temp_time_course.trial_identifier = temp_run_identifier_object

            # Data in seconds, data required to be in hours
            temp_time_course.time_vector = np.array(np.divide(data[0][1:], 3600))

            temp_time_course.data_vector = np.array(row[1:])
            experiment.titer_dict[temp_time_course.trial_identifier.unique_single_trial()] = copy.copy(temp_time_course)
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(experiment.titer_dict), tf - t0))
    experiment.parse_single_trial_dict(experiment.titer_dict)
    return data, t0

def parse_raw_data(data_format, data = None, file_name = None, experiment = None):
    if experiment is None:
        from .core.Experiment import Experiment
        experiment = Experiment()

    t0 = time.time()

    if data is None:
        if file_name is None:
            raise Exception('No data or file name given to load data from')

        # Get data from xlsx file
        data = get_data(file_name)
        print('Imported data from %s' % (file_name))

    # Import parsers
    parser_case_dict = {'spectromax_OD':spectromax_OD,
                        'tecan_OD': tecan_OD,
                        'default_titers':HPLC_titer_parser
                        }
    if data_format in parser_case_dict.keys():
        parser_case_dict[data_format](experiment,data,file_name)
    else:
        raise Exception('Parser %s not found', data_format)

    return experiment