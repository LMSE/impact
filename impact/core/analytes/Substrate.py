from .Base import *

class Substrate(TimeCourse):
    fit_type = None
    id = Column(Integer,ForeignKey('time_course.id'),primary_key=True)

    __tablename__ = 'analyte_substrate'
    __mapper_args__ = {
        'polymorphic_identity': 'substrate',
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._trial_identifier


    def curve_fit_data(self):
        from ..settings import settings
        verbose = settings.verbose

        if self.trial_identifier.analyte_type == 'substrate':
            print('Substrate curve fitting not implemented')
        else:
            raise Exception('Incorrect analyte_type')
