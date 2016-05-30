from scipy.signal import savgol_filter
from lmfit import Model

import numpy as np
import dill as pickle
import sqlite3 as sql

from fDAPI.TrialIdentifier import *


class Titer(object):
    def __init__(self):
        self.timePointList = []
        self._runIdentifier = RunIdentifier()

    @property
    def runIdentifier(self):
        return self._runIdentifier

    @runIdentifier.setter
    def runIdentifier(self, runIdentifier):
        self._runIdentifier = runIdentifier

    def addTimePoint(self, timePoint):
        raise (Exception("No addTimePoint method defined in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList) > 0:
            return self.timePointList[0].runIdentifier.strainID + \
                   self.timePointList[0].runIdentifier.identifier1 + \
                   self.timePointList[0].runIdentifier.identifier2 + \
                   str(self.timePointList[0].runIdentifier.replicate)
        elif self.runIdentifier.strainID != '':
            return self.runIdentifier.strainID + \
                   self.runIdentifier.identifier1 + \
                   self.runIdentifier.identifier2 + \
                   str(self.runIdentifier.replicate)
        else:
            raise Exception("No unique ID or time points in Titer()")

    def getReplicateID(self):
        return self.runIdentifier.strainID + self.runIdentifier.identifier1 + self.runIdentifier.identifier2


class CurveFitObject(object):
    """
    Wrapper for curve fitting objects

    Parameters:
        paramList: List of parameters, with initial guess, max and min values
            Each parameter is a dict with the following form
                {'name': str PARAMETER NAME,

                'guess': float or lambda function

                'max': float or lambda function

                'min': float or lambda function

                'vary' True or False}

        growthEquation: A function to fit with the following form:
            def growthEquation(t, param1, param2, ..): return f(param1,param2,..)

        method: lmfit method (slsqp, leastsq)
    """

    def __init__(self, paramList, growthEquation, method='slsqp'):
        self.paramList = paramList
        self.growthEquation = growthEquation
        self.gmod = Model(growthEquation)
        self.method = method

    def calcFit(self, t, data, method=None, **kwargs):
        # print('befor: ', method)
        if method is None: method = self.method
        # print('after: ', method)
        for param in self.paramList:
            # print(param)
            # Check if the parameter is a lambda function
            temp = dict()
            for hint in ['guess', 'min', 'max']:
                # print('hint: ',hint,'param[hint]: ',param[hint])
                if type(param[hint]) == type(lambda x: 0):
                    temp[hint] = param[hint](data)
                else:
                    temp[hint] = param[hint]
            self.gmod.set_param_hint(param['name'],
                                     value=temp['guess'],
                                     min=temp['min'],
                                     max=temp['max'])
            # self.gmod.print_param_hints()

        try:
            params = self.gmod.make_params()
        except Exception as e:
            # self.gmod.print_param_hints()
            print(data)
            print(e)

        result = self.gmod.fit(data, params, t=t, method=method, **kwargs)
        return result


class TimeCourse(Titer):
    """
    Child of :class:`~Titer` which contains curve fitting relevant to time course data
    """

    def __init__(self, removeDeathPhaseFlag=False, useFilteredData=False):
        Titer.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = dict()
        self.units = {'time': 'None',
                      'data': 'None'}

        self.gradient = []
        self.specific_productivity = []

        # Options
        self.removeDeathPhaseFlag = removeDeathPhaseFlag
        self.useFilteredDataFlag = useFilteredData

        self.deathPhaseStart = None
        self.blankSubtractionFlag = True

        self.savgolFilterWindowSize = 21  # Must be odd

        # Declare some standard curve fitting objects here
        self.curve_fit_dict = dict()

        keys = ['name', 'guess', 'min', 'max', 'vary']

        def growthEquation_generalized_logistic(t, A, k, C, Q, K, nu): return A + (
            (K - A) / (np.power((C + Q * np.exp(-k * t)), (1 / nu))))

        self.curve_fit_dict['growthEquation_generalized_logistic'] = CurveFitObject(
            [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
             dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 1, True])),
             dict(zip(keys, ['C', 1, None, None, True])),
             dict(zip(keys, ['Q', 0.01, None, None, True])),
             dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
             dict(zip(keys, ['nu', 1, None, None, True]))],
            growthEquation_generalized_logistic
        )

        def productionEquation_generalized_logistic(t, A, k, C, Q, K, nu): return A + (
            (K - A) / (np.power((C + Q * np.exp(-k * t)), (1 / nu))))

        self.curve_fit_dict['productionEquation_generalized_logistic'] = CurveFitObject(
            [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
             dict(zip(keys, ['k', lambda data: 50, lambda data: 0.001, 1000, True])),
             dict(zip(keys, ['C', 1, None, None, True])),
             dict(zip(keys, ['Q', 0.01, None, None, True])),
             dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
             dict(zip(keys, ['nu', 1, None, None, True]))],
            productionEquation_generalized_logistic
        )

        def janoschek(t, B, k, L, delta): return L - (L - B) * np.exp(-k * np.power(t, delta))

        self.curve_fit_dict['janoschek'] = CurveFitObject(
            [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
             dict(zip(keys, ['k', lambda data: 0.5, lambda data: 0.001, 200, True])),
             dict(zip(keys, ['delta', 1, -100, 100, True])),
             dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
            janoschek
        )

        # 5-param Richard's http://www.pisces-conservation.com/growthhelp/index.html?richards_curve.htm
        def richard_5(t, B, k, L, t_m, T): return B + L / np.power(1 + T * np.exp(-k * (t - t_m)), (1 / T))

        self.curve_fit_dict['richard_5'] = CurveFitObject(
            [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
             dict(zip(keys, ['k', lambda data: 0.5, 0.001, None, True])),
             dict(zip(keys, ['t_m', 10, None, None, True])),
             dict(zip(keys, ['T', 1, None, None, True])),
             dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
            richard_5
        )
        # Declare the default curve fit
        self.fit_type = 'growthEquation_generalized_logistic'

    @property
    def runIdentifier(self):
        return self._runIdentifier

    @Titer.runIdentifier.setter
    def runIdentifier(self, runIdentifier):
        self._runIdentifier = runIdentifier
        if runIdentifier.titerType == 'product':
            self.fit_type = 'productionEquation_generalized_logistic'

    @property
    def timeVec(self):
        return self._timeVec

    @timeVec.setter
    def timeVec(self, timeVec):
        self._timeVec = np.array(timeVec)

    @property
    def dataVec(self):
        if self.useFilteredDataFlag == True:
            return savgol_filter(self._dataVec, self.savgolFilterWindowSize, 3)
        else:
            return self._dataVec

    @dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = np.array(dataVec)
        self.gradient = np.gradient(self._dataVec) / np.gradient(self.timeVec)
        self.deathPhaseStart = len(dataVec)

        if self.removeDeathPhaseFlag == True:
            if np.max(dataVec) > 0.2:
                try:
                    if self.useFilteredDataFlag == True:
                        filteredData = savgol_filter(dataVec, 51, 3)
                    else:
                        filteredData = np.array(self._dataVec)
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
                            #     self.deathPhaseStart = len(dataVec)
                            # self._dataVec = dataVec
                            # print(len(self._dataVec)," ",len(self.timeVec))
                            # plt.plot(self._dataVec[0:self.deathPhaseStart],'r.')
                            # plt.plot(self._dataVec,'b-')
                            # plt.show()
                except Exception as e:
                    print(e)
                    print(dataVec)
                    # self.deathPhaseStart = len(dataVec)

            if self.deathPhaseStart == 0:
                self.deathPhaseStart = len(self.dataVec)

        if len(self.dataVec) > 5:
            self.calcExponentialRate()

    def commitToDB(self, singleTrialID, c=None, stat=None):
        if stat is None:
            stat_prefix = ''
        else:
            stat_prefix = '_' + stat
        c.execute(
            """INSERT INTO timeCourseTable""" + stat_prefix + """(singleTrial""" + stat_prefix + """ID, titerType, titerName, timeVec, dataVec, rate) VALUES (?, ?, ?, ?, ?, ?)""",
            (singleTrialID, self.runIdentifier.titerType, self.runIdentifier.titerName, self.timeVec.dumps(),
             self.dataVec.dumps(), pickle.dumps(self.rate))
        )

    def returnCurveFitPoints(self, t):
        return self.curve_fit_dict[self.fit_type].growthEquation(np.array(t), **self.rate)

    def addTimePoint(self, timePoint):
        self.timePointList.append(timePoint)
        if len(self.timePointList) == 1:
            self.runIdentifier = timePoint.runIdentifier
        else:
            for i in range(len(self.timePointList) - 1):
                if self.timePointList[i].runIdentifier.get_unique_ID_singleTrial() != self.timePointList[
                            i + 1].runIdentifier.get_unique_ID_singleTrial():
                    raise Exception("runIdentifiers don't match within the timeCourse object")

        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self._timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self._dataVec = np.array([timePoint.titer for timePoint in self.timePointList])

        if len(self.timePointList) > 6:
            self.calcExponentialRate()

    def calcExponentialRate(self):
        if self.runIdentifier.titerType == 'titer' or self.runIdentifier.titerType in ['substrate', 'product']:
            print(
                'Curve fitting for titers unimplemented in restructured curve fitting. Please see Depricated\depicratedCurveFittingCode.py')
            # gmod.set_param_hint('A', value=np.min(self.dataVec))
            # gmod.set_param_hint('B',value=2)
            # gmod.set_param_hint('C', value=1, vary=False)
            # gmod.set_param_hint('Q', value=0.1)#, max = 10)
            # gmod.set_param_hint('K', value = max(self.dataVec))#, max=5)
            # gmod.set_param_hint('nu', value=1, vary=False)
        elif self.runIdentifier.titerType in ['biomass']:
            # print('DPS: ',self.deathPhaseStart)
            # print(self.dataVec)
            # print(self.timeVec[0:self.deathPhaseStart])
            # print(self.dataVec[0:self.deathPhaseStart])
            # print('Started fit')
            # print(self.fit_type)
            result = self.curve_fit_dict[self.fit_type].calcFit(self.timeVec[0:self.deathPhaseStart],
                                                                self.dataVec[
                                                                0:self.deathPhaseStart])  # , fit_kws = {'maxfev': 20000, 'xtol': 1E-12, 'ftol': 1E-12})
            print('Finished fit')
            # self.rate = [0, 0, 0, 0, 0, 0]
            for key in result.best_values:
                self.rate[key] = result.best_values[key]

        else:
            print('Unidentified titer type:' + self.runIdentifier.titerType)

    def getFitParameters(self):
        return [[param['name'], self.rate[i]] for i, param in
                enumerate(self.curve_fit_dict[self.fit_type].paramList)]


class TimeCourseShell(TimeCourse):
    """
    This is a shell of :class:`~Titer` with an overidden setter to be used as a container
    """

    @TimeCourse.dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = dataVec


class EndPoint(Titer):
    """
    This is a child of :class:`~Titer` which does not calcualte any time-based data
    """

    def __init__(self, runID, t, data):
        Titer.__init__(self, runID, t, data)

    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)