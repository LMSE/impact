import numpy as np

from .Base import BaseAnalyteFeature
from .MassBalance import *
from .NormalizedData import *
from .ProductYield import *
from .SpecificProductivity import *








class COBRAModelFactory(BaseAnalyteFeature):
    def __init__(self):
        self.requires = ['biomass','substrate','product']

    def calculate(self):
        import cameo
        iJO = cameo.models.iJO1366


# class FeatureManager(object):
#     def __init__(self):
#         self.features = []
#         self.analytes_to_features = {}
#         self.analyte_types = ['biomass','substrate','product']
#         for analyte_type in self.analyte_types:
#             self.analytes_to_features[analyte_type] = []
#
#     def register_feature(self, feature):
#         self.features.append(feature)
#
#         analyte_types = ['biomass','substrate','product']
#         for analyte_type in analyte_types:
#             if analyte_type in feature.requires:
#                 self.analytes_to_features[analyte_type].append(feature)
#         setattr(self,feature.name,feature)
#
#     def add_analyte(self, analyte_data):
#         for analyte_type in self.analyte_types:
#             for feature in self.features:
#                 if feature in self.analyte_types[analyte_type]:
#                     feature.add_analyte(analyte_data)

# class TimeCourseStage(TimeCourse):
#     def __init__(self):
#         TimeCourse().__init__()
#
# @TimeCourse.stage_indices.setter
# def

# class SingleTrialDataShell(SingleTrial):
#     """
#     Object which overwrites the SingleTrial objects setters and getters, acts as a shell of data with the
#     same structure as SingleTrial
#     """
#
#     def __init__(self):
#         SingleTrial.__init__(self)
#
#     @SingleTrial.substrate.setter
#     def substrate(self, substrate):
#         self._substrate = substrate
#
#     @SingleTrial.OD.setter
#     def OD(self, OD):
#         self._OD = OD
#
#     @SingleTrial.products.setter
#     def products(self, products):
#         self._products = products