from .Base import *


class SpecificProductivityFactory(object):
    requires = ['substrate', 'product', 'biomass']
    name = 'specific_productivity'

    def __init__(self):
        self.biomass = None
        self.pending_analytes = []

    def add_analyte_data(self, analyte_data):
        if analyte_data.trial_identifier.analyte_type == 'biomass':
            self.biomass = analyte_data
            analyte_data.specific_productivity = SpecificProductivity(biomass=analyte_data,
                                                                      analyte=analyte_data)

            if len(self.pending_analytes) >= 1:
                for analyte_data in self.pending_analytes:
                    analyte_data.specific_productivity = SpecificProductivity(biomass=self.biomass,
                                                                              analyte=analyte_data)
                self.pending_analytes = []

        if analyte_data.trial_identifier.analyte_type in ['substrate', 'product']:
            if self.biomass is not None:
                analyte_data.specific_productivity = SpecificProductivity(biomass=self.biomass, analyte=analyte_data)
            else:
                self.pending_analytes.append(analyte_data)


class SpecificProductivity(BaseAnalyteFeature):
    def __init__(self, biomass, analyte):
        self.biomass = biomass
        self.analyte = analyte
        self.specific_productivity = None

    @property
    def data(self):
        if self.specific_productivity is None:
            self.calculate()

        return self.specific_productivity

    def calculate(self):
        """
        Calculate the specific productivity (dP/dt) given :math:`dP/dt = k_{Product} * X`
        """
        if self.biomass is None:
            return 'Biomass not defined'

        try:
            if len(self.analyte.data_vector) > 2:
                self.analyte.calculate()  # Need gradient calculated before accessing
                self.specific_productivity = self.analyte.gradient / self.biomass.data_vector
        except Exception as e:
            print(self.analyte.data_vector)
            raise Exception(e)
