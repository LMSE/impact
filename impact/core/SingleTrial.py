import pandas as pd

from .TrialIdentifier import SingleTrialIdentifier
from .features import *
from .AnalyteData import TimeCourse

from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, PickleType, Float, event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


class SingleTrial(Base):
    """
    Container for :class:`~TiterObject` to build a whole trial out of different measurements. E.g. one flask would
    contain data for biomass (OD), products (ethanol, acetate), substrates (glucose), fluorescence (gfpmut3, mCherry)
    """

    __tablename__ = 'single_trial'

    id = Column(Integer, primary_key=True)

    trial_identifier_id = Column(Integer, ForeignKey('single_trial_identifier.id'))
    _trial_identifier = relationship('SingleTrialIdentifier')

    analyte_dict = relationship('TimeCourse',
                                collection_class=attribute_mapped_collection('analyte_name'),
                                cascade='save-update, delete')

    stage_indices = Column(PickleType)

    parent_id = Column(Integer, ForeignKey('replicate_trial.id'))

    stage_parent_id = Column(Integer, ForeignKey('single_trial.id'))
    stages = relationship('SingleTrial', foreign_keys='SingleTrial.stage_parent_id')

    class_features = []
    analyte_types = ['biomass', 'substrate', 'product', 'reporter']

    @classmethod
    def register_feature(cls, feature):
        cls.class_features.append(feature)

    def __init__(self):
        # Trial identifier with relevant features common to the trial
        self._trial_identifier = None

        # Analyte objects
        self.analyte_dict = dict()

        # Dataframe containing all of the analytes with a common index
        self.analyte_df = pd.DataFrame()

        # Contains information about the stages used in the experiment, TODO
        self.stage_indices = None
        self.stage_list = None
        self.stages = []
        # Data normalized to different features, not serialized
        self.normalized_data = dict()

        # Register instances of feeatures
        self.features = []
        self.analytes_to_features = {}
        for analyte_type in SingleTrial.analyte_types:
            self.analytes_to_features[analyte_type] = []

        for feature in SingleTrial.class_features:
            self.features.append(feature())
            for analyte_type in SingleTrial.analyte_types:
                if analyte_type in feature.requires:
                    self.analytes_to_features[analyte_type].append(self.features[-1])

    #TODO, Fix this. Doesn't work. self.yields_df when yields_df doesn't exist
    def serialize(self):
        serialized_dict = {}

        if self.trial_identifier:
            serialized_dict['strain_id'] = self.trial_identifier.strain.name
            serialized_dict['id_1'] = self.trial_identifier.id_1
            serialized_dict['id_2'] = self.trial_identifier.id_2

        for analyte_name in self.analyte_dict:
            serialized_dict[analyte_name] = self.analyte_dict[analyte_name].serialize()

        serialized_dict['yields'] = self.yields_df.to_json()

        return serialized_dict

    # Setters and Getters
    @property
    def stages(self):
        return self._stages

    @stages.setter
    def stages(self, stages):
        """
        Creates stages when they are defined

        Parameters
        ----------
        stages : list of stage start and end lists [start_index, end_index]

        """
        self._stages = stages

        for stage in stages:
            stage = self.create_stage(stage)
            self.stage_list.append(stage)

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

        self.analyte_name = trial_identifier.analyte_name

    def calculate(self):
        for analyte_key in self.analyte_dict:
            self.analyte_dict[analyte_key].calculate()

    #Fixed this: SingleTrial does not have an attribute named product_names
    def normalize_data(self, normalize_to):
        for analyte in self.analyte_dict:
            self.normalized_data[analyte] = self.analyte_dict[analyte].data_vector\
                                            / self.analyte_dict[normalize_to].data_vector
    #TODO, Implement stages in avg/stdev too.
    def create_stage(self, stage_bounds):
        stage = SingleTrial()
        for analyte in self.analyte_dict:
            stage.add_analyte_data(self.analyte_dict[analyte].create_stage(stage_bounds))
        self.stages.append(stage)
        return stage

    def summary(self, printFlag=False):
        summary = dict()

        for analyte_type in ['substrate', 'products', 'biomass']:
            summary[analyte_type] = [str(analyte_data) for analyte_data in self.analyte_dict.values() if
                                     analyte_data.trial_identifier.analyte_type == analyte_type]
        #summary['number_of_data_points'] = len(self._t)
        summary['run_identifier'] = self.trial_identifier.summary(['strain_id', 'id_1', 'id_2',
                                                                   'replicate_id'])

        if printFlag:
            print(summary)

        return summary

    def calculate_mass_balance(self, OD_gdw=None, initial_substrate=0, calculateFBACO2=False):
        """
        Calculate a mass balance given the supplied substrate and products

        Parameters
        ----------
        OD_gdw : float
            The correlation betwen OD_gdw and OD600
        calculateFBACO2 : bool
            Flag to calculate the CO2 using FBA (not implemented yet)
        """
        # if calculateFBACO2:
        #     import cobra
        #
        #     # Load the COBRA model
        #     ...
        #
        #     # Convert the common names to COBRA model names
        #     commonNameCobraDictionary = {'Lactate'  : ...,
        #                                  'Ethanol'  : ...,
        #                                  'Acetate'  : ...,
        #                                  'Formate'  : ...,
        #                                  'Glycolate': ...,
        #                                  'Glucose'  : ...,
        #                                  'Succinate': ...
        #                                  }
        #
        #     # Get the molar mass from COBRA model and covert the grams to mmol
        #     substrate = model.metabolites.get_by_id(substrate_name)
        #     # substrate_mmol = substrate.formulaWeight()
        #     # substrate.lower_bound = self.substrate.data_vector[-1]
        #     # substrate.upper_bound = self.substrate.data_vector[-1]
        #     productsCOBRA = dict()
        #     for key in self.yields:
        #         modelMetID = commonNameCobraDictionary[key]
        #         productsCOBRA[key] = model.metabolites.get_by_id(modelMetID)
        #
        #     # Set the bounds
        #     ...
        #
        #     # Run the FBA and return the CO2
        #     ...

        if type(OD_gdw) is None:
            # Parameters for E. coli
            OD_gdw = 0.33  # Correlation for OD to gdw for mass balance

        # self.substrate_consumed
        # sorting analytes into OD, products, etc.
        self.products=[]
        for analyte in self.analyte_dict.values():
            if analyte.type == 'biomass':
                self.OD = analyte
            if analyte.type == 'product':
                self.products.append(analyte)
            if analyte.type == 'substrate':
                self.substrate = analyte
        substrate_consumed = self.substrate.data_vector - initial_substrate
        if self.OD is not None:
            # Calc mass of biomass
            biomass_gdw = self.OD.data_vector / OD_gdw
        else:
            biomass_gdw = None

        # Calculate the mass of products consumed
        totalProductMass = np.sum([self.products[productKey].data_vector for productKey in self.products], axis=0)

        # Calculate the mass balance (input-output)
        if biomass_gdw is None:   biomass_gdw = np.zeros(
            [len(substrate_consumed)])  # If this isn't defined, set biomass to zero
        if len(biomass_gdw) == len(totalProductMass) and len(biomass_gdw) == len(substrate_consumed):
            massBalance = substrate_consumed - totalProductMass - biomass_gdw
        else:
            massBalance = substrate_consumed[-1] - totalProductMass[-1] - biomass_gdw[-1]
        return {'substrate_consumed': substrate_consumed,
                'totalProductMass'  : totalProductMass,
                'biomass_gdw'       : biomass_gdw,
                'massBalance'       : massBalance}

    def calculate_ODE_fit(self):
        """
        WIP to fit the data to ODEs
        """
        biomass = self.analyte_dict[self.biomass_name].data_vector
        biomass_rate = np.gradient(self.analyte_dict[self.biomass_name].data_vector) / np.gradient(
            self.analyte_dict[self.biomass_name].time_vector)
        self.analyte_dict[self.substrate_name]
        self.analyte_dict[self.product_names]

        def dFBA_functions(y, t, rate):
            # Append biomass, substrate and products in one list
            exchange_reactions = biomass_flux + substrate_flux + product_flux
            # y[0]           y[1]
            dydt = []
            for exchange_reaction in exchange_reactions:
                if y[1] > 0:  # If there is substrate
                    dydt.append(exchange_reaction * y[0])
                else:  # If there is not substrate
                    dydt.append(0)
            return dydt

        import numpy as np
        from scipy.integrate import odeint

        # Let's assign the data to these variables
        biomass_flux = [model.solution.x_dict[biomass_keys[0]]]

        substrate_flux = [model.solution.x_dict[substrate_keys[0]]]

        product_flux = [model.solution.x_dict[key] for key in product_keys]

        exchange_keys = biomass_keys + substrate_keys + product_keys

        # Now, let's build our model for the dFBA
        def dFBA_functions(y, t, biomass_flux, substrate_flux, product_flux):
            # Append biomass, substrate and products in one list
            exchange_reactions = biomass_flux + substrate_flux + product_flux
            # y[0]           y[1]
            dydt = []
            for exchange_reaction in exchange_reactions:
                if y[1] > 0:  # If there is substrate
                    dydt.append(exchange_reaction * y[0])
                else:  # If there is not substrate
                    dydt.append(0)
            return dydt

        # Now let's generate the data
        sol = odeint(dFBA_functions, y0, t,
                     args=([flux * np.random.uniform(1 - noise, 1 + noise) for flux in biomass_flux],
                           [flux * np.random.uniform(1 - noise, 1 + noise) for flux in
                            substrate_flux],
                           [flux * np.random.uniform(1 - noise, 1 + noise) for flux in
                            product_flux]))

        dFBA_profile = {key: [row[i] for row in sol] for i, key in enumerate(exchange_keys)}

    # @event.listens_for(TimeCourse, 'load')
    def add_analyte_data(self, analyte_data):
        """
        Add a :class:`~TiterObject`

        Parameters
        ----------
        analyte_data : :class:`~TiterObject`
            A titer object to be added

        """
        from .settings import settings
        live_calculations = settings.live_calculations

        # Check if this analyte already exists
        if analyte_data.trial_identifier.analyte_name in self.analyte_dict:
            print('Duplicate ReplicateTrialIdentifier: ',
                  str(analyte_data.trial_identifier))
            print('Original ReplicateTrialIdentifier: ',
                  str(self.analyte_dict[analyte_data.trial_identifier.analyte_name].trial_identifier))
            raise Exception('A duplicate titer was added to the single trial,\n'
                            'Make sure replicates are defined properly,\n'
                            'Duplicate ReplicateTrialIdentifier: ',
                            str(analyte_data.trial_identifier))

        self.analyte_dict[analyte_data.trial_identifier.analyte_name] = analyte_data

        # Add relevant analyte types to calculate features
        for feature in self.features:
            if analyte_data.trial_identifier.analyte_type in feature.requires:
                feature.add_analyte_data(analyte_data)

        # check if trial identifiers match
        if len(self.analyte_dict) == 1:
            self.trial_identifier = SingleTrialIdentifier()
            for attr in ['strain', 'media', 'environment', 'id_1', 'id_2', 'replicate_id']:
                setattr(self.trial_identifier, attr, getattr(analyte_data.trial_identifier, attr))
        else:
            for attr in ['strain', 'media', 'environment', 'id_1', 'id_2', 'replicate_id']:
                # Check for no match
                if str(getattr(self.trial_identifier, attr)) != str(getattr(analyte_data.trial_identifier, attr)):
                    raise Exception('Trial identifiers do not match at the following attribute: '
                                    + attr
                                    + ' val 1: '
                                    + str(getattr(self.trial_identifier, attr))
                                    + ' val 2: '
                                    + str(getattr(analyte_data.trial_identifier, attr)))
                # If match, ensure attrs refer to same instance
                else:
                    setattr(analyte_data.trial_identifier, attr, getattr(self.trial_identifier, attr))

        # Set the parent
        analyte_data.parent = self

        self.trial_identifier.time = None

        # Pandas support
        temp_analyte_df = pd.DataFrame()
        temp_analyte_df[analyte_data.trial_identifier.analyte_name] = analyte_data.pd_series

        # Merging the dataframes this way will allow different time indices for different analytes
        self.analyte_df = pd.merge(self.analyte_df, temp_analyte_df, left_index=True, right_index=True, how='outer')
        self.t = self.analyte_df.index

    def link_identifiers(self, trial_identifier, attrs=['strain', 'media', 'environment']):
        for attr in attrs:
            setattr(self.trial_identifier, attr, getattr(trial_identifier, attr))


# Register known features
for feature in [ProductYieldFactory, SpecificProductivityFactory, ODNormalizedDataFactory]:
    SingleTrial.register_feature(feature)
