from .Base import *
class Biomass(TimeCourse):


    id = Column(Integer,ForeignKey('time_course.id'),primary_key=True)

    # def __init__(self):
        # TimeCourse.__init__()
        # self._trial_identifier

    __tablename__ = 'analyte_biomass'
    __mapper_args__ = {
        'polymorphic_identity': 'biomass',
    }


    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier



    def curve_fit_data(self):
        if self.trial_identifier.analyte_type == 'biomass':
            from ..settings import settings
            verbose = settings.verbose
            self.find_death_phase(self.data_vector)

            # from scipy.interpolate import InterpolatedUnivariateSpline
            # spl = InterpolatedUnivariateSpline(self.time_vector, self.data_vector)
            # spl.set_smoothing_factor(0.2)
            # spl_grad = np.gradient(spl(self.time_vector)) / np.gradient(self.time_vector)
            # self.fit_params['growth_rate'] = max(spl_grad)
            #
            # import matplotlib.pyplot as plt
            # plt.figure()
            # plt.plot(self.time_vector,self.data_vector,'o')
            # plt.plot(self.time_vector,spl(self.time_vector),lw=2)
            # plt.show()
            # return max(spl_grad)

            if verbose:
                print('Started fit')
                print('Death phase start: ', self.death_phase_start)

            result = curve_fit_dict[self.fit_type].calcFit(self.time_vector[0:self.death_phase_start],
                                                           self.data_vector[0:self.death_phase_start])
            # ,fit_kws = {'xatol':1E-10, 'fatol':1E-10})  # , fit_kws = {'maxfev': 20000, 'xtol': 1E-12, 'ftol': 1E-12})
            if verbose: print('Finished fit')

            for key in result.best_values:
                temp_param = FitParameter(key, result.best_values[key])
                self.fit_params[key] = temp_param  # result.best_values[key]

            if verbose:
                import matplotlib.pyplot as plt
                plt.figure()
                plt.plot(self.time_vector[0:self.death_phase_start], self.data_vector[0:self.death_phase_start], 'bo')
                plt.plot(self.time_vector[0:self.death_phase_start], result.best_fit, 'r-')

            if verbose: print(result.fit_report())
        else:
            raise Exception('Incorrect analyte_type')
