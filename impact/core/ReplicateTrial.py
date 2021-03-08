# coding=utf-8

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .AnalyteData import TimeCourse, FitParameter
from .SingleTrial import SingleTrial
from .TrialIdentifier import ReplicateTrialIdentifier

from ..database import Base
from sqlalchemy import Column, Integer, ForeignKey, PickleType, String, event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


class ReplicateTrial(Base):
    """
    This object stores SingleTrial objects and calculates statistics on these replicates for each of the
    titers which are stored within it
    """

    __tablename__ = 'replicate_trial'

    id = Column(Integer, primary_key=True)

    avg_id = Column(Integer, ForeignKey('single_trial.id'))
    avg = relationship('SingleTrial', uselist=False, foreign_keys=[avg_id])

    std_id = Column(Integer, ForeignKey('single_trial.id'))
    std = relationship('SingleTrial', uselist=False, foreign_keys=[std_id])

    single_trial_dict = relationship('SingleTrial',
                                     collection_class=attribute_mapped_collection('trial_identifier.replicate_id'),
                                     foreign_keys='SingleTrial.parent_id')

    trial_identifier_id = Column(Integer, ForeignKey('replicate_trial_identifier.id'))
    trial_identifier = relationship('ReplicateTrialIdentifier')

    stage_parent_id = Column(Integer, ForeignKey('replicate_trial.id'))
    stages = relationship('ReplicateTrial')

    blank_id = Column(Integer, ForeignKey('single_trial.id'))
    blank = relationship('SingleTrial', uselist=False, foreign_keys=[blank_id])

    parent = relationship('Experiment')  # ,back_populates="replicate_trials")
    parent_id = Column(Integer, ForeignKey('experiment.id'))

    bad_replicates = Column(PickleType)
    replicate_ids = Column(PickleType)

    unique_id = Column(String)

    def __init__(self, **kwargs):
        self.avg = SingleTrial()
        self.std = SingleTrial()
        self.t = None

        self.single_trial_dict = {}

        self.trial_identifier = ReplicateTrialIdentifier()
        self.bad_replicates = dict()
        self.replicate_df = dict()

        self.stages = []
        self.features = []
        self.blank_subtraction_flag = False
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    @property
    def unique_id(self):
        return self.trial_identifier.unique_replicate_trial()

    @property
    def single_trials(self):
        return list(self.single_trial_dict.values())

    def calculate(self):
        # commented 2 lines below because stage calculation is done once in expt already. no need to do it again
        # for stage in self.stages:
        #    stage.calculate()

        for single_trial in self.single_trial_dict.values():
            single_trial.calculate()

        if self.blank and not self.blank_subtraction_flag:  self.substract_blank()
        self.calculate_statistics()

    def create_stage(self, stage_bounds):
        if stage_bounds is None:
            raise Exception('No stage_bounds provided')

        stage = ReplicateTrial()
        for replicate_id in self.single_trial_dict:
            # if self.blank:
            #     blank_stage = self.blank.create_stage(stage_bounds)
            #     stage.set_blank(blank_stage)
            single_trial = self.single_trial_dict[replicate_id]
            stage.add_replicate(single_trial.create_stage(stage_bounds))
        #Added this to ensure avg and std are calculated for the stages
        stage.calculate_statistics()
        self.stages.append(stage)

        return stage

    def get_normalized_data(self, normalize_to):
        new_replicate = ReplicateTrial()
        for replicate_id in self.single_trial_dict:
            single_trial = self.single_trial_dict[replicate_id]
            single_trial.normalize_data(normalize_to)
            new_replicate.add_replicate(single_trial)
        self = new_replicate

    def check_replicate_unique_id_match(self):
        """
        Ensures that the uniqueIDs match for all te replicate_id experiments
        """
        replicate_ids = list(self.single_trial_dict.keys())
        replicate_ids.sort()
        for i in range(len(self.single_trial_dict) - 1):
            if self.single_trial_dict[replicate_ids[i]].trial_identifier.unique_replicate_trial() \
                    != self.single_trial_dict[replicate_ids[i + 1]].trial_identifier.unique_replicate_trial():
                raise Exception(
                    "the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

    # @event.listens_for(SingleTrial, 'load')
    def add_replicate(self, single_trial):
        """
        Add a SingleTrial object to this list of replicates

        Parameters
        ----------
        single_trial : :class:`~SingleTrial`
            Add a SingleTrial
        """
        from .settings import settings
        live_calculations = settings.live_calculations

        if str(single_trial.trial_identifier.replicate_id) in self.single_trial_dict.keys():
            print(single_trial.trial_identifier)
            print(self.trial_identifier)
            raise Exception('Duplicate replicate id: '
                            + str(single_trial.trial_identifier.replicate_id)
                            + '.\nCurrent ids: '
                            + str(self.single_trial_dict.keys()))

        if single_trial.trial_identifier.replicate_id is None:
            single_trial.trial_identifier.replicate_id = 1

        # Get info from single trial
        self.single_trial_dict[str(single_trial.trial_identifier.replicate_id)] = single_trial
        # Adding a bad replicates list for each analyte
        for analyte in single_trial.analyte_dict:
            if analyte not in self.bad_replicates.keys():
                self.bad_replicates[analyte] = []

        if len(self.single_trial_dict) == 1:
            self.t = self.single_trial_dict[str(single_trial.trial_identifier.replicate_id)].t
            self.trial_identifier = single_trial.trial_identifier.get_replicate_trial_trial_identifier()
        else:
            for attr in ['strain', 'media', 'environment', 'id_1', 'id_2']:
                setattr(single_trial.trial_identifier, attr, getattr(self.trial_identifier, attr))

                for analyte in single_trial.analyte_dict.values():
                    for attr in ['strain', 'media', 'environment', 'id_1', 'id_2']:
                        setattr(analyte.trial_identifier, attr, getattr(self.trial_identifier, attr))

        self.check_replicate_unique_id_match()

        # Extract features from single trial
        for feature in single_trial.features:
            if len(self.features) == 0:
                self.features.append(feature)
            elif not isinstance(feature, tuple(type(feature) for feature in self.features)):
                self.features.append(feature)

        if live_calculations:
            self.calculate_statistics()

    def calculate_statistics(self):
        """
        Calculates the statistics on the SingleTrial objects
        """
        unique_analytes = self.get_analytes()

        for analyte in unique_analytes:
            self.avg.analyte_dict[analyte] = TimeCourse()
            self.std.analyte_dict[analyte] = TimeCourse()

            # Copy a relevant trial identifier
            first_st = [single_trial for single_trial in self.single_trial_dict.values()
                        if analyte in single_trial.analyte_dict][0]
            try:
                self.avg.analyte_dict[analyte].trial_identifier = \
                    first_st \
                        .analyte_dict[analyte] \
                        .trial_identifier. \
                        get_analyte_data_statistic_identifier()

                self.std.analyte_dict[analyte].trial_identifier = \
                    first_st \
                        .analyte_dict[analyte] \
                        .trial_identifier. \
                        get_analyte_data_statistic_identifier()
            except Exception as e:
                print(first_st.analyte_dict)
                raise Exception(e)

            self.replicate_df[analyte] = pd.DataFrame()

            # Get all the trials with the analyte
            trial_list = [single_trial for single_trial in self.single_trials if analyte in single_trial.analyte_dict]

            # Merge the dataframes for relevant trials
            for trial in trial_list:
                self.replicate_df[analyte] = pd.merge(self.replicate_df[analyte],
                                                      pd.DataFrame({str(trial.trial_identifier.replicate_id):
                                                                        trial.analyte_dict[analyte].pd_series}),
                                                      left_index=True,
                                                      right_index=True,
                                                      how='outer')
            # Remove outliers
            self.prune_bad_replicates(analyte)

            # Set statistics
            self.avg.analyte_dict[analyte].pd_series = self.replicate_df[analyte].mean(axis=1)
            self.std.analyte_dict[analyte].pd_series = self.replicate_df[analyte].std(axis=1)

            if self.blank_subtraction_flag and analyte in self.blank_subtracted_analytes:
                self.std.analyte_dict[analyte].pd_series = np.sqrt(np.square(self.std.analyte_dict[analyte].pd_series)
                                                            + np.square(self.blank.std.analyte_dict[analyte].pd_series))
            #Assume that stdev for all values <0 is simply 0 since negative values are forced to be 0.
            #Negative values of any analyte in this context is not possible
            #self.std.analyte_dict[analyte].pd_series[self.avg.analyte_dict[analyte].pd_series<=0] = 0
            # Calculate statistics for features

            for feature in self.features:

                if feature.name in ['od_normalized_data','specific_productivity']:

                    trial_list = [single_trial
                                  for single_trial in self.single_trials
                                  if analyte in single_trial.analyte_dict
                                  and feature.name in single_trial.analyte_dict[analyte].__dict__]
                    if len(trial_list)>0:
                        biomass_labels = ['OD600', 'OD700', 'OD660']
                        biomass_analyte = [analyte_name for analyte_name in trial_list[0].analyte_dict if
                                           analyte_name in biomass_labels][0]
                        single_trial_var = []
                        single_trial_data = []
                        for trial in trial_list:
                            feature_object = getattr(trial.analyte_dict[analyte], feature.name)
                            feature_data = feature_object.data
                            if feature_data is not None:
                                single_trial_data.append(feature_data)
                            if self.blank:
                                with np.errstate(divide='ignore'):

                                    temp_var = np.square(feature_data)*(np.square(self.blank.std.analyte_dict[analyte].pd_series\

                                               /trial.analyte_dict[analyte].pd_series)+
                                                np.square(self.blank.std.analyte_dict[biomass_analyte].pd_series
                                                          /trial.analyte_dict[biomass_analyte].pd_series))
                                    temp_var[trial.analyte_dict[analyte].pd_series == 0] = 0
                                    temp_var[trial.analyte_dict[biomass_analyte].pd_series == 0] = 0
                                    single_trial_var.append(temp_var)
                        if single_trial_data:
                            rep_mean = sum(single_trial_data)/len(trial_list)
                        else:
                            rep_mean = None

                        #This is the variance due to individual normalized datapoints
                        rep_var = pd.Series(data=np.var(single_trial_data,axis=0),index=trial_list[-1].analyte_dict[analyte].time_vector)
                        # Variance on dataset due to blanks is average of individual standard deviation squared.
                        # Total variance is variance due to blanks + variance between individual normalized datapoints
                        if self.blank:
                            rep_var = sum(single_trial_var)/np.square(len(single_trial_var)) + rep_var

                        setattr(self.std.analyte_dict[analyte], feature.name, np.sqrt(rep_var).values)
                        setattr(self.avg.analyte_dict[analyte], feature.name, rep_mean)

                else:
                    # Get all the analytes with the feature
                    trial_list = [single_trial
                                  for single_trial in self.single_trials
                                  if analyte in single_trial.analyte_dict
                                  and feature.name in single_trial.analyte_dict[analyte].__dict__]

                    # Merge them all, in case they don't share the same index (missing data)
                    df = pd.DataFrame()
                    for trial in trial_list:
                        df = df.merge(pd.DataFrame({
                            str(trial.trial_identifier.replicate_id):
                                pd.Series(getattr(trial.analyte_dict[analyte], feature.name).data,
                                          index=trial.analyte_dict[analyte].time_vector)}),
                            left_index=True, right_index=True, how='outer')

                    # Calculate and set the feature statistics
                    setattr(self.avg.analyte_dict[analyte], feature.name, pd.Series(df.mean(axis=1)).values)
                    setattr(self.std.analyte_dict[analyte], feature.name, pd.Series(df.std(axis=1)).values)


        # Calculate fit param stats
        for analyte in unique_analytes:
            for stat, calc in zip(['avg', 'std'], [np.mean, np.std]):
                # If a fit_params exists, calculate the stats
                if None not in [single_trial.analyte_dict[analyte].fit_params
                                if analyte in single_trial.analyte_dict else None
                                for single_trial in self.single_trials]:
                    temp = dict()
                    for param in self.single_trial_dict[list(self.single_trial_dict.keys())[0]].analyte_dict[
                        analyte].fit_params:
                        temp[param] = FitParameter(param, calc(
                            [self.single_trial_dict[replicate_id].analyte_dict[analyte].fit_params[
                                 param].parameter_value
                             for replicate_id in self.single_trial_dict
                             if self.single_trial_dict[
                                 replicate_id].trial_identifier.replicate_id not in self.bad_replicates[analyte]]))

                    getattr(self, stat).analyte_dict[analyte].fit_params = temp
                    # else:
                    #     print([self.single_trial_dict[replicate_id].analyte_dict[analyte].fit_params
                    #            for replicate_id in self.single_trial_dict
                    #            if analyte in self.single_trial_dict[replicate_id].analyte_dict])

    def get_analytes(self):
        # Get all unique analytes
        unique_analytes = []
        for replicate_id in self.single_trial_dict:
            single_trial = self.single_trial_dict[replicate_id]
            for titer in single_trial.analyte_dict:
                unique_analytes.append(titer)
        unique_analytes = list(set(unique_analytes))
        return unique_analytes

    def prune_bad_replicates(self, analyte):  # Remove outliers
        from .settings import settings
        verbose = settings.verbose
        max_fraction_replicates_to_remove = settings.max_fraction_replicates_to_remove
        outlier_cleaning_flag = settings.outlier_cleaning_flag
        std_deviation_cutoff = settings.std_deviation_cutoff
        # http://stackoverflow.com/questions/23199796/detect-and-exclude-outliers-in-pandas-dataframe
        df = self.replicate_df[analyte]
        col_names = list(df.columns.values)
        backup = self.replicate_df[analyte]

        if outlier_cleaning_flag and len(col_names) > 2:
            outlier_removal_method = 'iterative_removal'
            # Method one for outlier removal
            if outlier_removal_method == 'z_score':
                fraction_outlier_pts = np.sum(np.abs(stats.zscore(df)) < 1, axis=0) / len(df)
                print(fraction_outlier_pts)
                bad_replicates = [col_name for i, col_name in enumerate(col_names) if fraction_outlier_pts[i] < 0.8]
                # good_replicates = (np.abs(stats.zscore(df)) < 3).all(axis=0)  # Find any values > 3 std from mean
                # if bad_replicates.any():
                print(bad_replicates)
                if bad_replicates:
                    good_replicate_cols = [col_names[x] for x, col_name in enumerate(bad_replicates)
                                           if col_name not in bad_replicates]
                else:
                    good_replicate_cols = col_names
                bad_replicate_cols = [col_names[x] for x, col_name in enumerate(bad_replicates)
                                      if col_name in bad_replicates]
                print('good', good_replicate_cols)
                print('bad: ', bad_replicate_cols)

            # method 2 for outlier removal (preferred)
            # this method removal each replicate one by one, and if the removal of a replicate reduces the std
            # by a certain threshold, the replicate is flagged as removed
            if outlier_removal_method == 'iterative_removal':
                bad_replicate_cols = []
                good_replicate_cols = df.columns.values

                # Determine the max number of replicates to remove
                for _ in range(int(len(self.single_trial_dict) * max_fraction_replicates_to_remove)):
                    # A value between 0 and 1, > 1 means removing the replicate makes the yield worse

                    # df = pd.DataFrame({key: np.random.randn(5) for key in ['a', 'b', 'c']})
                    std_by_mean = np.mean(abs(df.std(axis=1)/df.mean(axis=1)))
                    temp_std_by_mean = {}
                    for temp_remove_replicate in list(df.columns.values):
                        indices = [replicate for i, replicate in enumerate(df.columns.values) if
                                   replicate != temp_remove_replicate]
                        temp_remove_replicate_df = df[indices]
                        temp_mean = temp_remove_replicate_df.mean(axis=1)
                        temp_std = temp_remove_replicate_df.std(axis=1)
                        temp_std_by_mean[temp_remove_replicate] = np.mean(abs(temp_std / temp_mean))

                    temp_min_val = min([temp_std_by_mean[key] for key in temp_std_by_mean])
                    if abs(temp_min_val-std_by_mean) >= std_deviation_cutoff and temp_min_val < std_by_mean:
                        bad_replicate_cols.append(
                            [key for key in temp_std_by_mean if temp_std_by_mean[key] == temp_min_val][0])

                    good_replicate_cols = [key for key in temp_std_by_mean if key not in bad_replicate_cols]
                    df = df[good_replicate_cols]
                self.replicate_df[analyte] = df[good_replicate_cols]
                self.bad_replicates[analyte] = bad_replicate_cols
            # Plot the results of replicate removal
            if verbose:
                plt.figure()
                try:
                    if good_replicate_cols:
                        plt.plot(backup[good_replicate_cols], 'r')
                    if bad_replicate_cols:
                        plt.plot(backup[bad_replicate_cols], 'b')
                    plt.title(self.trial_identifier.unique_replicate_trial())
                except Exception as e:
                    print(e)
            del backup

    def set_blank(self, replicate_trial):
        self.blank = replicate_trial

    def substract_blank(self):
        # Check which analytes have blanks defined
        analytes_with_blanks = self.blank.get_analytes()

        # Remove from each analyte and then redo calculations
        self.blank_subtracted_analytes = []

        # for blank_analyte in analytes_with_blanks:
        for single_trial in self.single_trials:
            for blank_analyte in analytes_with_blanks:
                if blank_analyte in single_trial.analyte_dict:
                    single_trial.analyte_dict[blank_analyte].pd_series = \
                        single_trial.analyte_dict[blank_analyte].pd_series \
                        - self.blank.avg.analyte_dict[blank_analyte].pd_series
                    single_trial.analyte_dict[blank_analyte].generate_time_point_list()
                    #single_trial.analyte_dict[blank_analyte].data_vector = \
                    #    single_trial.analyte_dict[blank_analyte].data_vector.clip(min = 0)
                self.blank_subtracted_analytes.append(blank_analyte)
        self.blank_subtracted_analytes = list(set(self.blank_subtracted_analytes))
        self.blank_subtraction_flag = True

    def get_unique_analytes(self):
        return list(set([analyte
                         for single_trial_key in self.single_trial_dict
                         for analyte in self.single_trial_dict[single_trial_key].analyte_dict]
                        )
                    )

    def link_identifiers(self, trial_identifier, attrs=['strain', 'media', 'environment']):
        for attr in attrs:
            setattr(self.trial_identifier, attr, getattr(trial_identifier, attr))
