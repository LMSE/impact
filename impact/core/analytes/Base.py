
from ..TrialIdentifier import TimeCourseIdentifier
from ...curve_fitting import *

import pandas as pd

from scipy.signal import savgol_filter

from ...database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import event


class TimePoint(Base):
    __tablename__ = 'time_point'

    time_point_type = Column(String)

    __mapper_args__ = {
        'polymorphic_on': time_point_type,
        'polymorphic_identity':'raw'
    }

    id = Column(Integer, primary_key=True)
    trial_identifier_id = Column(Integer,ForeignKey('time_course_identifier.id'))
    trial_identifier = relationship('TimeCourseIdentifier')
    time = Column(Float)
    data = Column(Float)
    parent_id = Column(Integer,ForeignKey('time_course.id'))
    parent = relationship('TimeCourse')

    use_in_analysis = Column(Boolean)

    def __init__(self, trial_identifier=None, time=None, data=None):
        self.trial_identifier = TimeCourseIdentifier() if trial_identifier is None else trial_identifier
        self.time = time
        self.data = data

    def get_unique_timepoint_id(self):
        return self.trial_identifier.unique_time_point()


class TimeCourse(Base):
    """
    Child of :class:`~AnalyteData` which contains curve fitting relevant to time course data
    """
    __tablename__ = 'time_course'

    discriminator = Column(String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer,primary_key = True)

    trial_identifier_id = Column(Integer, ForeignKey('time_course_identifier.id'))
    _trial_identifier = relationship('TimeCourseIdentifier')

    time_points = relationship('TimePoint')
    gradient_points = relationship('GradientTimePoint')
    specific_productivity_points = relationship('SpecificProductivityTimePoint')

    calculations_uptodate = Column(Boolean)
    fit_params = relationship('FitParameter',
                              collection_class=attribute_mapped_collection('parameter_name'),
                              cascade="all, delete-orphan")

    stages = relationship('TimeCourseStage')

    parent_id = Column(Integer, ForeignKey('single_trial.id'))
    parent = relationship('SingleTrial',uselist=False)

    analyte_name = Column(String)
    analyte_type = Column(String)

    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'time_course',
        'polymorphic_on': type
    }

    @reconstructor
    def __init__(self, **kwargs):
        # Get the default parameters
        from ..settings import settings

        self.pd_series = None

        if 'time_points' in kwargs:
            for time_point in kwargs['time_points']:
                self.add_timepoint(time_point)

        # Overwrite user-set parameters
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])

        # Used to store the single_trial to which each analyte instance belongs
        self.parent = None  # type SingleTrial

        # Keep track of whether or not calculations need to be updated
        self.calculations_uptodate = False

        self.fit_params = dict()

        self._gradient = []

        # Options
        self.remove_death_phase_flag = settings.remove_death_phase_flag
        self.use_filtered_data = settings.use_filtered_data
        self.minimum_points_for_curve_fit = settings.minimum_points_for_curve_fit
        self.savgol_filter_window_size = settings.savgolFilterWindowSize

        # Init variables
        self.death_phase_start = None
        self.blankSubtractionFlag = True

        self.stages = []
        self._stage_indices = None

        # Declare the default curve fit
        self.fit_type = settings.fit_type

    def __str__(self):
        return str(self.trial_identifier.unique_analyte_data())

    @property
    def unique_id(self):
        return ','.join([str(self.trial_identifier.strain),str(self.trial_identifier.media),str(self.trial_identifier.id_1),
                         str(self.trial_identifier.id_2), str(self.trial_identifier.id_3), str(self.trial_identifier.replicate_id)])

    def serialize(self):
        serialized_dict = {'data'    : self.pd_series.to_json(), 'fit_params': self.fit_params,
                           'gradient': list(self.gradient)}

        try:
            serialized_dict['specific_productivity'] = list(self.specific_productivity)
        except Exception as e:
            print(e)

        serialized_dict['analyte_name'] = self.trial_identifier.analyte_name
        serialized_dict['analyte_type'] = self.trial_identifier.analyte_type

        options = {}
        for option in ['remove_death_phase_flag', 'use_filtered_data', 'minimum_points_for_curve_fit']:
            options[option] = getattr(self,option)
        serialized_dict['options'] = options

        return serialized_dict

    @property
    def stage_indices(self):
        return self._stage_indices

    @stage_indices.setter
    def stage_indices(self, stage_indices):
        self._stage_indices = stage_indices
        for stage_bounds in stage_indices:
            self.stages.append(self.create_stage(stage_bounds))

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

    @property
    def time_vector(self):
        if hasattr(self,'pd_series') and self.pd_series is not None:
            return np.array(self.pd_series.index)
        return None

    @time_vector.setter
    def time_vector(self, time_vector):
        if self.pd_series is None:
            self.pd_series = pd.Series(index=time_vector)
        else:
            self.pd_series.index = time_vector

        if sum(self.pd_series.index.duplicated()) > 0:
            print(self.pd_series.index)
            raise Exception('Duplicate time points found, this is not supported')

        # Fill time point list
        self.generate_time_point_list()

    @property
    def data_vector(self):
        from ..settings import settings

        # Filter data to smooth noise from the signal
        if settings.use_filtered_data and len(self.pd_series)>self.savgol_filter_window_size:
            return savgol_filter(np.array(self.pd_series), self.savgol_filter_window_size, 3)
        else:
            return np.array(self.pd_series)

    @data_vector.setter
    def data_vector(self, data_vector):
        from ..settings import settings
        live_calculations = settings.live_calculations

        # Check if an index has already been added
        if self.pd_series is None:
            self.pd_series = pd.Series(data_vector)
        else:
            self.pd_series = pd.Series(data_vector, index=self.pd_series.index)

        # Convert vectors to list format (for db)
        self.generate_time_point_list()

        # Instantiate death phase to be not detected (last point of the vector)
        self.death_phase_start = len(data_vector)
        if live_calculations:   self.calculate()

    @property
    def gradient(self):
        if self._gradient == []:
            if self.time_vector is not None and len(self.time_vector) > 2:
                self._gradient = np.gradient(self.data_vector) / np.gradient(self.time_vector)

        return self._gradient

    def generate_time_point_list(self):
        if self.time_points:
            for time_point in self.time_points:
                time_point.data = self.pd_series[time_point.time]
        else:
            self.time_points = [TimePoint(time=time, data=data, trial_identifier = self.trial_identifier)
                            for time, data in zip(self.pd_series.index, self.pd_series)]

    def calculate(self):
        from ..settings import settings
        perform_curve_fit = settings.perform_curve_fit

        if self.time_vector is not None and len(self.time_vector) > 2:
            self._gradient = np.gradient(self.data_vector) / np.gradient(self.time_vector)
        if self.remove_death_phase_flag:
            self.find_death_phase(self.data_vector)

        if len(self.data_vector) > self.minimum_points_for_curve_fit and perform_curve_fit:
            self.curve_fit_data()

    def find_death_phase(self, data_vector):
        from ..settings import settings
        use_filtered_data = settings.use_filtered_data
        verbose = settings.verbose
        self.death_phase_start = self.find_death_phase_static(data_vector,
                                                              use_filtered_data = use_filtered_data,
                                                              verbose = verbose)

    @staticmethod
    def find_death_phase_static(data_vector, use_filtered_data=False, verbose=False, hyper_parameter = 1):
        # The hyper_parameter determines the number of points
        # which need to have a negative diff to consider it death phase

        from ..settings import settings
        savgol_filter_window_size = settings.savgolFilterWindowSize
        death_phase_start = len(data_vector)

        # Check if there is a reasonable difference between the min and max of the curve
        if (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector) > 1:
            if verbose: print('Growth range: ', (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector))

            if use_filtered_data:
                filteredData = savgol_filter(data_vector, savgol_filter_window_size, 3)
            else:
                filteredData = np.array(data_vector)
            diff = np.diff(filteredData)

            count = 0
            flag = 0

            for i in range(len(diff) - hyper_parameter):
                # Check if the diff is negative (e.g. death fit_params > growth fit_params)
                if diff[i] <= 0:
                    flag = 1
                    count += 1
                    if count > hyper_parameter:
                        death_phase_start = i - hyper_parameter
                        break
                elif count > 0:
                    # Reset counter if death_phase increases again
                    count = 1
                    flag = 0

        if death_phase_start == 0:
            death_phase_start = len(data_vector)

        return death_phase_start

    def create_stage(self, stage_bounds):
        stage = TimeCourseStage(self)#, bounds = stage_bounds)
        stage.trial_identifier = self.trial_identifier
        self.stages.append(stage)
        # Note pandas slices by index value, not index
        stage.pd_series = self.pd_series[stage_bounds[0]:stage_bounds[1]]
        return stage

    def data_curve_fit(self, t):
        return curve_fit_dict[self.fit_type].growthEquation(np.array(t), **self.fit_params)

    @event.listens_for(TimePoint, 'load')
    def add_timepoint(self, time_point):
        from ..settings import settings
        live_calculations = settings.live_calculations

        time_point.parent = self

        self.time_points.append(time_point)
        if len(self.time_points) == 1:
            self.trial_identifier = time_point.trial_identifier
            self.pd_series = pd.Series([time_point.data],index=[time_point.time])
        else:
            if self.time_points[-1].trial_identifier.unique_single_trial() \
                    != self.time_points[-2].trial_identifier.unique_single_trial():
                print(self.time_points[-1].trial_identifier)
                print(self.time_points[-2].trial_identifier)

                raise Exception("Attempted to add time point with non-matching identifier")

            # Check if ordering is broken
            if self.time_points[-1].time < self.time_points[-2].time:
                self.time_points.sort(key=lambda timePoint: timePoint.time)


        if sum(self.pd_series.index.duplicated()) > 0:
            print(self.pd_series)
            print(self.trial_identifier)
            print(time_point.trial_identifier)
            raise Exception('Duplicate time points found, this is not supported - likely an identifier input error')

    def curve_fit_data(self):
        raise Exception('This must be implemented in a child')


class GradientTimePoint(TimePoint):
    __mapper_args__ = {
        'polymorphic_identity':'gradient'
    }


class SpecificProductivityTimePoint(TimePoint):
    __mapper_args__ = {
        'polymorphic_identity':'specific_productivity'
    }


class TimeCourseStage(TimeCourse):
    __tablename__ = 'time_course_stage'

    stage_parent_id = Column(Integer, ForeignKey('time_course.id'), primary_key=True)
    stage_parent = relationship('TimeCourse',uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'time_course_stage',
    }

    def __init__(self, parent, *args, **kwargs):
        self.stage_parent = parent
        # print(type(parent))

        super().__init__(*args, **kwargs)

class FitParameter(Base):
    __tablename__ = 'fit_parameters'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('time_course.id'))
    parameter_name = Column(String)
    parameter_value = Column(Float)

    def __init__(self, name, value):
        self.parameter_name = name
        self.parameter_value = value
