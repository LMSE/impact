from scipy.signal import savgol_filter

import numpy as np
import dill as pickle
import sqlite3 as sql

from .TrialIdentifier import TrialIdentifier
from .curve_fitting import *
from .Options import *

class AnalyteData(object):
    def __init__(self):
        self.timePointList = []
        self._trial_identifier = TrialIdentifier()

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

    def add_timepoint(self, timePoint):
        raise (Exception("No addTimePoint method defined in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList) > 0:
            return ''.join([str(getattr(self.timePointList[0].trial_identifier,attr))
                            for attr in ['strain_id','id_1','id_2','replicate_id']])
            # '.strain_id + \
            #        self.timePointList[0].trial_identifier.id_1 + \
            #        self.timePointList[0].trial_identifier.id_2 + \
            #        str(self.timePointList[0].trial_identifier.replicate_id)
        elif self.trial_identifier.strain_id != '':
            return self.trial_identifier.strain_id + \
                   self.trial_identifier.id_1 + \
                   self.trial_identifier.id_2 + \
                   str(self.trial_identifier.replicate_id)
        else:
            raise Exception("No unique ID or time points in AnalyteData()")

    def getReplicateID(self):
        return self.trial_identifier.strain_id + self.trial_identifier.id_1 + self.trial_identifier.id_2

class TimeCourse(AnalyteData):
    """
    Child of :class:`~AnalyteData` which contains curve fitting relevant to time course data
    """

    def __init__(self, options = Options(), removeDeathPhaseFlag=False, useFilteredData=False):
        AnalyteData.__init__(self)
        self.time_vector = None
        self._data_vector = None
        self.rate = dict()
        self.units = {'time': 'None',
                      'data': 'None'}

        self.gradient = []
        self.specific_productivity = []

        # Options
        self.removeDeathPhaseFlag = options.remove_death_phase_flag
        self.useFilteredDataFlag = options.use_filtered_data
        self.minimum_points_for_curve_fit = options.minimum_points_for_curve_fit

        self.deathPhaseStart = None
        self.blankSubtractionFlag = True

        self.savgolFilterWindowSize = 21  # Must be odd

        self.stages = []
        self._stage_indices = None

        # Declare the default curve fit
        self.fit_type = 'gompertz'

    @property
    def stage_indices(self):
        return self._stage_indices

    @stage_indices.setter
    def stage_indices(self, stage_indices):
        self._stage_indices = stage_indices
        for stage_bounds in stage_indices:
            self.stages.append(self.create_stage(stage_bounds))

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @AnalyteData.trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier
        if trial_identifier.analyte_type == 'product':
            self.fit_type = 'productionEquation_generalized_logistic'

    @property
    def time_vector(self):
        return self._timeVec

    @time_vector.setter
    def time_vector(self, timeVec):
        self._timeVec = np.array(timeVec)

    @property
    def data_vector(self):
        if self.useFilteredDataFlag == True:
            return savgol_filter(self._data_vector, self.savgolFilterWindowSize, 3)
        else:
            return self._data_vector

    @data_vector.setter
    def data_vector(self, dataVec):
        self._data_vector = np.array(dataVec)
        self.gradient = np.gradient(self._data_vector) / np.gradient(self.time_vector)
        self.deathPhaseStart = len(dataVec)

        if self.removeDeathPhaseFlag:
            self.find_death_phase(dataVec)

        if len(self.data_vector) > self.minimum_points_for_curve_fit:
            self.curve_fit_data()

    def find_death_phase(self, dataVec):
        if np.max(dataVec) > 0.2:
            try:
                if self.useFilteredDataFlag == True:
                    filteredData = savgol_filter(dataVec, 51, 3)
                else:
                    filteredData = np.array(self._data_vector)
                diff = np.diff(filteredData)

                count = 0
                flag = 0

                for i in range(len(diff) - 10):
                    if diff[i] < 0:
                        flag = 1
                        count += 1
                        if count > 10:
                            self.deathPhaseStart = i - 10
                            break
                    elif count > 0:
                        count = 1
                        flag = 0
                        # if flag == 0:
                        #     self.deathPhaseStart = len(data_vector)
                        # self._data_vector = data_vector
                        # print(len(self._data_vector)," ",len(self.time_vector))
                        # plt.plot(self._data_vector[0:self.deathPhaseStart],'r.')
                        # plt.plot(self._data_vector,'b-')
                        # plt.show()
            except Exception as e:
                print(e)
                print(dataVec)
                # self.deathPhaseStart = len(data_vector)
        if self.deathPhaseStart == 0:
            self.deathPhaseStart = len(self.data_vector)

    def db_commit(self, singleTrialID, c=None, stat=None):
        if stat is None:
            stat_prefix = ''
        else:
            stat_prefix = '_' + stat
        c.execute(
            """INSERT INTO timeCourseTable""" + stat_prefix + """(singleTrial""" + stat_prefix + """ID, titerType, analyte_name, time_vector, data_vector, rate) VALUES (?, ?, ?, ?, ?, ?)""",
            (singleTrialID, self.trial_identifier.analyte_type, self.trial_identifier.analyte_name, self.time_vector.dumps(),
             self.data_vector.dumps(), pickle.dumps(self.rate))
        )

    def summary(self, print=False):
        summary = dict()
        summary['time_vector'] = self.time_vector
        summary['data_vector'] = self.data_vector
        summary['number_of_data_points'] = len(self.time_vector)
        summary['run_identifier'] = self.trial_identifier.summary(['strain_id', 'id_1', 'id_2',
                                                                'analyte_name', 'titerType', 'replicate_id'])

        if print:
            print(summary)

        return summary

    def create_stage(self, stage_bounds):
        stage = TimeCourse()
        stage.trial_identifier = self.trial_identifier
        stage.time_vector = self.time_vector[stage_bounds[0]:stage_bounds[1] + 1]
        stage.data_vector = self.data_vector[stage_bounds[0]:stage_bounds[1] + 1]
        if len(self.gradient) > 0:
            stage.gradient = self.gradient[stage_bounds[0]:stage_bounds[1] + 1]
        if len(self.specific_productivity) > 0:
            stage.specific_productivity = self.specific_productivity[stage_bounds[0]:stage_bounds[1] + 1]

        return stage

    def data_curve_fit(self, t):
        return curve_fit_dict[self.fit_type].growthEquation(np.array(t), **self.rate)

    def add_timepoint(self, timePoint):
        self.timePointList.append(timePoint)
        if len(self.timePointList) == 1:
            self.trial_identifier = timePoint.trial_identifier
        else:
            for i in range(len(self.timePointList) - 1):
                if self.timePointList[i].trial_identifier.get_unique_for_SingleTrial() != self.timePointList[
                            i + 1].trial_identifier.get_unique_for_SingleTrial():
                    raise Exception("trial_identifiers don't match within the timeCourse object")

        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self._timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self._data_vector = np.array([timePoint.titer for timePoint in self.timePointList])

        if len(self.timePointList) > 6:
            self.gradient = np.gradient(self._data_vector) / np.gradient(self.time_vector)
            # self.data_vector = np.array([timePoint.titer for timePoint in self.timepoint_list])
            # pass
            # print('Skipping exponential rate calculation')

            # self.curve_fit_data()

    def curve_fit_data(self):
        if self.trial_identifier.analyte_type == 'titer' or self.trial_identifier.analyte_type in ['substrate', 'product']:
            pass
            # print(
            #     'Curve fitting for titers unimplemented in restructured curve fitting. Please see Depricated\depicratedCurveFittingCode.py')
            # gmod.set_param_hint('A', value=np.min(self.data_vector))
            # gmod.set_param_hint('B',value=2)
            # gmod.set_param_hint('C', value=1, vary=False)
            # gmod.set_param_hint('Q', value=0.1)#, max = 10)
            # gmod.set_param_hint('K', value = max(self.data_vector))#, max=5)
            # gmod.set_param_hint('nu', value=1, vary=False)
        elif self.trial_identifier.analyte_type in ['biomass']:
            # print('DPS: ',self.deathPhaseStart)
            # print(self.data_vector)
            # print(self.time_vector[0:self.deathPhaseStart])
            # print(self.data_vector[0:self.deathPhaseStart])
            print('Started fit')
            # print(self.fit_type)
            print(self.deathPhaseStart)
            result = curve_fit_dict[self.fit_type].calcFit(self.time_vector[0:self.deathPhaseStart],
                                                                self.data_vector[0:self.deathPhaseStart])  # , fit_kws = {'maxfev': 20000, 'xtol': 1E-12, 'ftol': 1E-12})
            print('Finished fit')
            # self.rate = [0, 0, 0, 0, 0, 0]
            for key in result.best_values:
                self.rate[key] = result.best_values[key]

        else:
            print('Unidentified titer type:' + self.trial_identifier.analyte_type)
            print('Ensure that the trial identifier is described before adding data. This will allow curve fitting'
                  'to be appropriate to the analyte type.')

    def get_fit_parameters(self):
        return [[param['name'], self.rate[i]] for i, param in
                enumerate(curve_fit_dict[self.fit_type].paramList)]


# class TimeCourseStage(TimeCourse):
#     def __init__(self):
#         TimeCourse.__init__()

class TimeCourseShell(TimeCourse):
    """
    This is a shell of :class:`~AnalyteData` with an overidden setter to be used as a container
    """

    @TimeCourse.data_vector.setter
    def data_vector(self, dataVec):
        self._data_vector = dataVec


class EndPoint(AnalyteData):
    """
    This is a child of :class:`~AnalyteData` which does not calcualte any time-based data
    """

    def __init__(self, runID, t, data):
        AnalyteData.__init__(self, runID, t, data)

    def add_timepoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)