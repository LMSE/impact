"""
Methods for curve fitting
"""

from .core import CurveFitObject
import numpy as np

keys = ['name', 'guess', 'min', 'max', 'vary']
curve_fit_dict = {}

"""
Generalized logistic
"""
def generalized_logistic(t, A, growth_rate, C, Q, K, nu):
    return A + ( (K - A) / (np.power((C + Q * np.exp(-growth_rate * t)), (1 / nu))))
curve_fit_dict['productionEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['growth_rate', lambda data: 50, lambda data: 0.001, 1000, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    generalized_logistic,
)
curve_fit_dict['growthEquation_generalized_logistic'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['growth_rate', lambda data: 0.5, lambda data: 0.001, 1, True])),
     dict(zip(keys, ['C', 1, None, None, True])),
     dict(zip(keys, ['Q', 0.01, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 1, None, None, True]))],
    generalized_logistic
)

curve_fit_dict['growthEquation_generalized_logistic_2'] = CurveFitObject(
    [dict(zip(keys, ['A', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     # starting titer
     dict(zip(keys, ['growth_rate', 1, 0, 2, True])),  # Growth fit_params
     dict(zip(keys, ['C', 1, None, None, False])),
     dict(zip(keys, ['Q', 0.5, None, None, True])),
     dict(zip(keys, ['K', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True])),
     dict(zip(keys, ['nu', 0.5, None, None, True]))],
    generalized_logistic,
    method='leastsq'
)

class Parameter(object):
    # name = 0
    # guess = 0
    # min = 0
    # max = 0

    def __init__(self, name=None, guess=None, min=None, max=None):
        self.name = name
        self.guess = guess
        self.min = min
        self.max = max


# from lmfit import Model
# class FitMethod(object):
#     """
#     Wrapper for curve fitting objects
#
#     Parameters:
#         paramList: List of parameters, with initial guess, max and min values
#             Each parameter is a dict with the following form
#                 {'name': str PARAMETER NAME,
#                 'guess': float or lambda function
#                 'max': float or lambda function
#                 'min': float or lambda function
#                 'vary' True or False}
#         growthEquation: A function to fit with the following form:
#             def growthEquation(t, param1, param2, ..): return f(param1,param2,..)
#
#         method: lmfit method (slsqp, leastsq)
#     """
#
#     def __init__(self, parameter_list, fit_equation, method='slsqp'):
#         self.parameter_list = parameter_list
#         self.fit_equation = fit_equation
#         self.gmod = Model(fit_equation)
#         self.method = method
#
#     def calculate_fit(self, t, data, **kwargs):
#         if 'method' not in kwargs:
#             method = self.method
#         else:
#             method = kwargs['method']
#
#         for param in self.parameter_list:
#             # Check if the parameter is a lambda function
#             temp = dict()
#
#             for attr in ['guess', 'min', 'max']:
#                 # print('hint: ',hint,'param[hint]: ',param[hint])
#                 if type(getattr(param,attr)) == type(lambda x: 0):
#                     temp[attr] = getattr(param, attr)(data)
#                 else:
#                     temp[attr] = getattr(param,attr)
#
#             self.gmod.set_param_hint(param.name,
#                                      value=temp['guess'],
#                                      min=temp['min'],
#                                      max=temp['max'],
#                                      vary=param['vary'])
#         try:
#             params = self.gmod.make_params()
#         except Exception as e:
#             print(data)
#             print(e)
#
#         result = self.gmod.fit(data, params, t=t, method=method, **kwargs)
#         result.fit_report()
#         return result
#
# growth_rate = Parameter('growth_rate',guess=0.01,min=0)
# X0 = Parameter('X0',guess=lambda data: min(data))
# Xf = Parameter ('Xf',guess=lambda data: max(data))
# delta = Parameter('delta',guess=1)
# janoshek = FitMethod(parameter_list = [growth_rate, X0, growth_rate, Xf, delta])



"""
janoschek
"""
def janoschek(t, B, growth_rate, L, delta): return L - (L - B) * np.exp(-growth_rate * np.power(t, delta))
curve_fit_dict['janoschek'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['growth_rate', lambda data: 0.001, None, 5, True])),
     dict(zip(keys, ['delta', 1, None, None, True])),
     dict(zip(keys, ['L', max, lambda data: max(data), lambda data: 2 * max(data), True]))],
    janoschek,
    method='slsqp'
)

curve_fit_dict['janoschek_no_limits'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, None, None, True])),
     dict(zip(keys, ['growth_rate', 1, None, None, True])),
     dict(zip(keys, ['delta', 1, None, None, True])),
     dict(zip(keys, ['L', np.max, None, None, True]))],
    janoschek,
    method='slsqp'
)

"""
5-param Richard's
http://www.pisces-conservation.com/growthhelp/index.html?richards_curve.htm
"""
def richard_5(t, B, growth_rate, L, t_m, T): return B + L / np.power(1 + T * np.exp(-growth_rate * (t - t_m)), (1 / T))
curve_fit_dict['richard_5'] = CurveFitObject(
    [dict(zip(keys, ['B', np.min, lambda data: 0.975 * np.min(data), lambda data: 1.025 * np.min(data), True])),
     dict(zip(keys, ['growth_rate', lambda data: 0.5, 0.001, None, True])),
     dict(zip(keys, ['t_m', 10, None, None, True])),
     dict(zip(keys, ['T', 1, None, None, True])),
     dict(zip(keys, ['L', max, lambda data: 0.975 * max(data), lambda data: 1.025 * max(data), True]))],
    richard_5,
    # method='slsqp'
)

"""
Gompertz growth equation
http://www.ncbi.nlm.nih.gov/pmc/articles/PMC184525/pdf/aem00087-0379.pdf
"""
def gompertz(t, A, growth_rate, lam):
    return A * np.exp(-np.exp(growth_rate * np.e / A * (lam - t)))
curve_fit_dict['gompertz'] = CurveFitObject(
    [dict(zip(keys, ['A', np.max, lambda data: 0.975 * np.max(data), lambda data: 1.025 * np.max(data), True])),
     dict(zip(keys, ['growth_rate', 1, 0, 5, True])),
     dict(zip(keys, ['lam', 2, 0, None, True]))],
    gompertz,
    method='slsqp'
)

"""
3 parameter growth curve (sigmoid)
"""
def three_param_growth(t,A,B,growth_rate):
    return A * B / (A + (B - A) * np.exp(-growth_rate * t))
curve_fit_dict['three_param'] = CurveFitObject(
    [dict(zip(keys, ['A', 0.05, None, None, True])),
     dict(zip(keys, ['B', 1, None, None, True])),
     dict(zip(keys, ['growth_rate', 0.5, None, None, True]))],
    three_param_growth,
    method='leastsq'
)

def fit_data(t, param_dict, fit_type = 'gompertz'):

    if fit_type == 'gompertz':
        return gompertz(t, param_dict['A'].parameter_value, param_dict['growth_rate'].parameter_value,
                        param_dict['lam'].parameter_value)

    if fit_type == 'three_param':
        return three_param_growth(t, param_dict['A'].parameter_value, param_dict['B'].parameter_value,
                                  param_dict['growth_rate'].parameter_value)

    if fit_type == 'richard_5':
        return richard_5(t, param_dict['B'].parameter_value, param_dict['growth_rate'].parameter_value,

                         param_dict['L'].parameter_value, param_dict['t_m'].parameter_value,
                         param_dict['T'].parameter_value)

    if fit_type == 'janoschek':
        return janoschek(t, param_dict['B'].parameter_value, param_dict['growth_rate'].parameter_value,
                         param_dict['L'].parameter_value, param_dict['delta'].parameter_value)

    if fit_type in ['growthEquation_generalized_logistic_2','productionEquation_generalized_logistic','growthEquation_generalized_logistic']:
        return generalized_logistic(t, param_dict['A'].parameter_value, param_dict['growth_rate'].parameter_value,

                                    param_dict['C'].parameter_value, param_dict['Q'].parameter_value,
                                    param_dict['K'].parameter_value, param_dict['nu'].parameter_value)

    return None