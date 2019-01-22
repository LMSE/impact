from .Base import *

class Reporter(TimeCourse):
    fit_type = None

    # def __init__(self):
        # TimeCourse.__init__()
        # self._trial_identifier
    id = Column(Integer,ForeignKey('time_course.id'),primary_key=True)
    __tablename__ = 'analyte_reporter'
    __mapper_args__ = {
        'polymorphic_identity': 'reporter',
    }
    def curve_fit_data(self):
        from ..settings import settings
        verbose = settings.verbose

        if self.trial_identifier.analyte_type == 'reporter':
            print('Reporter curve fitting not implemented')
        else:
            raise Exception('Incorrect analyte_type')
