from .Base import *
import numpy as np


class ProductYield(BaseAnalyteFeature):
    def __init__(self, substrate, product):
        self.substrate = substrate
        self.product = product
        self.product_yield = None
        self.substrate_consumed = None

    @property
    def data(self):
        self.calculate()
        return self.product_yield

    def calculate(self):
        self.calculate_substrate_consumed()
        try:
            self.product_yield = np.divide(
                self.product.data_vector - np.tile(self.product.data_vector[0], [len(self.product.data_vector)]),
                self.substrate_consumed
            )
        except Exception as e:
            print(self.product)
            print(self.product.data_vector)
            raise Exception(e)

    def calculate_substrate_consumed(self):
        self.substrate_consumed = np.array(
            [(self.substrate.data_vector[0] - dataPoint)
             for dataPoint in self.substrate.data_vector]
        )


class ProductYieldFactory(BaseAnalyteFeatureFactory):
    requires = ['substrate', 'product', 'biomass']
    name = 'product_yield'

    def __init__(self):
        self.products = []
        self.substrate = None

    def add_analyte_data(self, analyte_data):
        if analyte_data.trial_identifier.analyte_type == 'substrate':
            if self.substrate is None:
                self.substrate = analyte_data

                if len(self.products) > 0:
                    for product in self.products:
                        product.product_yield = ProductYield(substrate=self.substrate, product=product)

                    # Once we've processed the waiting products we can delete them
                    self.product = []
            else:
                raise Exception('No support for Multiple substrates: ',
                                str(self.substrate.trial_identifier),
                                ' ',
                                str(analyte_data.trial_identifier))

        if analyte_data.trial_identifier.analyte_type in ['biomass', 'product']:
            if self.substrate is not None:
                analyte_data.product_yield = ProductYield(substrate=self.substrate, product=analyte_data)
            else:
                # Hold on to the product until a substrate is defined
                self.products.append(analyte_data)
