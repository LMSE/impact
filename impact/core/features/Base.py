# Features
class BaseAnalyteFeature(object):
    """
    Base multi analyte feature. Use this to create new features.
    A feature is anything calcaulted from multiple analytes
    """
    def __init__(self):
        self.analyte_list = []
        self.name = ''

    @property
    def data(self):
        return 'Not implemented'


class BaseAnalyteFeatureFactory(object):
    requires = None
    name = None

    def __init__(self):
        """
        Initialize any required variables here.
        """
        raise Exception('Must be implemented in child')

    def add_analyte_data(self, analyte_data):
        """
        Function called when new analyte is added. If an analyte is required for this feature, ensure to save or
        use analyte. Do not manipulate raw analyte data.
        Parameters
        ----------
        analyte_data

        Returns
        -------

        """
        pass