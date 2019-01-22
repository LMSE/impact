from .Base import *


class ODNormalizedData(BaseAnalyteFeature):
    # The constructor should accept all required analytes as parameters
    def __init__(self, biomass, analyte):
        self.biomass = biomass
        self.analyte = analyte
        self.od_normalized_data = None


    # This data property assures that the data is returned, or calculated as needed
    @property
    def data(self):
        if self.od_normalized_data is None:
            self.calculate()
        return self.od_normalized_data

    # This is where the property is actually calculated and set
    def calculate(self):
        self.od_normalized_data = self.analyte.data_vector / self.biomass.data_vector



# The feature factory watches for those analytes
class ODNormalizedDataFactory(BaseAnalyteFeatureFactory):
    # define what the feature
    requires = ['biomass', 'reporter', 'product', 'substrate']
    name = 'od_normalized_data'

    # constructor should initialize variables until all required analytes are present,
    # this will ensure that despite the order analytes are added, feature will be calculated appropriately
    def __init__(self):
        self.biomass = None
        self.pending_analytes = []

    # define how to handle new analytes
    def add_analyte_data(self, analyte_data):
        if analyte_data.trial_identifier.analyte_type == 'biomass':
            self.biomass = analyte_data
            analyte_data.od_normalized_data = ODNormalizedData(biomass=analyte_data, analyte=analyte_data)
            if len(self.pending_analytes) >= 1:
                for analyte_data in self.pending_analytes:
                    analyte_data.od_normalized_data = ODNormalizedData(biomass=self.biomass, analyte=analyte_data)
                self.pending_analytes = []

        if analyte_data.trial_identifier.analyte_type in ['product', 'substrate', 'reporter']:
            if self.biomass:
                analyte_data.od_normalized_data = ODNormalizedData(biomass=self.biomass, analyte=analyte_data)
            else:
                self.pending_analytes.append(analyte_data)



class NormalizedData(BaseAnalyteFeature):
    """
    Normalizes a given analyte to another
    """

    def __init__(self, analyte, normalization_analyte):
        self.analyte = analyte
        self.normalization_analyte = normalization_analyte

    @property
    def data(self):
        return self.analyte / self.normalization_analyte


class NormalizedDataFactory(BaseAnalyteFeatureFactory):
    requires = ['product', 'substrate', 'biomass']
    name = 'normalized_data'

    def __init__(self):
        """
        Initialize any required variables here.
        """
        self.analytes = []
        raise Exception('Must be implemented in child')

    def add_analyte_data(self, analyte):
        """
        Function called when new analyte is added. If an analyte is required for this feature, ensure to save or
        use analyte. Do not manipulate raw analyte data.
        Parameters
        ----------
        analyte_data

        Returns
        -------

        """
        self.analytes.append(analyte)

        for analyte in self.analytes:
            analyte.normalized_data = NormalizedData(analyte, self.analytes[-1])
