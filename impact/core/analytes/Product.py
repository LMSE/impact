from .Base import *

class Product(TimeCourse):
    fit_type = 'productionEquation_generalized_logistic'
    id = Column(Integer,ForeignKey('time_course.id'),primary_key=True)

    # def __init__(self):
        # TimeCourse.__init__()
        # self._trial_identifier
    __tablename__ = 'analyte_product'
    __mapper_args__ = {
        'polymorphic_identity': 'product',
    }
    def curve_fit_data(self):
        from ..settings import settings
        verbose = settings.verbose

        if self.trial_identifier.analyte_type == 'product':
            raise Exception('Product curve fitting not implemented')
        else:
            raise Exception('Incorrect analyte_type')
