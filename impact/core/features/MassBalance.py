from .Base import *
import numpy as np


class MassBalance(BaseAnalyteFeature):
    """
    Base multi analyte feature. Use this to create new features.
    """

    def __init__(self):
        self.analyte_list = []
        self.name = ''

    @property
    def data(self):
        return 'Not implemented'


class MassBalance(BaseAnalyteFeature):
    def __init__(self, substrate, product=None, biomass=None):
        self.substrate = substrate
        self.product = product
        self.biomass = biomass
        # self.product_yield = None
        # self.substrate_consumed = None

    @property
    def data(self):
        if self.product is None and self.biomass is None:
            raise Exception('Cannot balance mass without anything produced')
        else:
            self.calculate()
        return self.mass_balance

    def calculate(self):
        # self.mass_balance = self.substrate - [analyte]


        # Check if id is bigg
        pass

        # Calculate mass
        pass


        # self.calculate_substrate_consumed()
        # try:
        #     self.product_yield = np.divide(
        #         self.product.data_vector - np.tile(self.product.data_vector[0],[len(self.product.data_vector)]),
        #         self.substrate_consumed
        #     )
        # except Exception as e:
        #     print(self.product)
        #     print(self.product.data_vector)
        #     raise Exception(e)

    def calculate_substrate_consumed(self):
        self.substrate_consumed = np.array(
            [(self.substrate.data_vector[0] - dataPoint)
             for dataPoint in self.substrate.data_vector]
        )


class MassBalanceFactory(object):
    def __init__(self):
        self.requires = ['biomass', 'substrate', 'product']
