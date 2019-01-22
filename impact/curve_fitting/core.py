"""
Functions for curve fitting
"""

import numpy as np
from lmfit import Model


# class EquationFit(object):
#     def __init__(self):
#         parameter_list = []
#         equation = []
#         method = []
#
#     def calculate_parameters(self):
#

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

    def calcFit(self, t, data, **kwargs):
        if 'method' not in kwargs:
            method = self.method
        else:
            method = kwargs['method']

        for param in self.paramList:
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
                                     max=temp['max'],
                                     vary=param['vary'])
        try:
            params = self.gmod.make_params()
        except Exception as e:
            print(data)
            print(e)

        result = self.gmod.fit(data, params, t=t, method=method, **kwargs)
        result.fit_report()
        return result

class GrowthRateSplineExtraction(object):
    """
    Wrapper for curve fitting objects using splines

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

    def get_growth_rate(self, t, data, **kwargs):
        from scipy.interpolate import InterpolatedUnivariateSpline
        import numpy as np
        spl = InterpolatedUnivariateSpline(t,data)
        spl_grad = np.gradient(spl(t))/np.gradient(t)

        return max(spl_grad)
