from ..database import Base

from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from warnings import warn

class Knockout(Base):
    __tablename__ = 'knockout'
    id = Column(Integer, primary_key=True)
    gene = Column(String)
    parent = Column(Integer, ForeignKey('strain.id'))

    def __str__(self):
        return str(self.gene)

class Plasmid(Base):
    __tablename__ = 'plasmid'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    strain = Column(Integer, ForeignKey('strain.id'))

    def __str__(self):
        return str(self.name)

class Strain(Base):
    """
    Model for a strain
    """

    __tablename__ = 'strain'

    id = Column(Integer, primary_key=True)
    nickname = Column(String)
    formal_name = Column(String)
    plasmids = relationship('Plasmid')
    knockouts = relationship('Knockout')
    parent = Column(Integer,ForeignKey('strain.id'))


    def __init__(self, name='',**kwargs):
        for key in kwargs:
            if key in ['nickname','formal_name', 'plasmid_1','plasmid_2','plasmid_3']:
                setattr(self,key,kwargs[key])
            else:
                setattr(self,key,None)

        if name != '':
            self.nickname = name
        # models.Model.__init__(self, *args, **kwargs)


    def __str__(self):
        plasmid_summ = '+'.join([str(plasmid) for plasmid in self.plasmids])

        if self.nickname is None:
            nick = ''
        else:
            nick = self.nickname
        if plasmid_summ :
            return nick+'+'+plasmid_summ
        else:
            return nick

    @property
    def unique_id(self):
        return self.name

class MediaComponent(Base):
    """
    Media component many-to-many relationship
    """

    __tablename__ = 'media_component'
    id = Column(Integer,primary_key=True)
    name = Column(String,unique=True)

    def __init__(self, name):
        self.name = name

class ComponentConcentration(Base):
    """
    Concentration of all components for all media
    """
    __tablename__ = 'comp_conc'

    id = Column(Integer, primary_key=True)

    media_id = Column(String, ForeignKey('media.id'))
    media = relationship("Media", cascade='all')

    component_name = Column(String, ForeignKey('media_component.name'))
    media_component = relationship("MediaComponent", cascade='all')

    concentration = Column(Float)

    def __init__(self, component, concentration, unit=None, **kwargs):
        for key in kwargs:
            if key in ['media']:
                setattr(self,key,kwargs[key])

        self.media_component = component
        self.concentration = concentration

    def _convert_units(self):
        if not self.units_converted:
            if self._unit == '%':
                self._concentration *= 10
            elif self._unit == 'g/L':
                pass
            else:
                raise Exception('Only g/L and % supported')

class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer,primary_key=True)
    nickname = Column(String)
    name = Column(String)
    component_concentrations = relationship('ComponentConcentration', cascade = 'all')
    parent = Column(Integer,ForeignKey('media.name'))

    def __init__(self, concentration=None, unit=None, **kwargs):
        for key in kwargs:
            if key in ['parent','nickname','name']:
                setattr(self,key,kwargs[key])

        self.component_concentrations = []

        self._concentration = concentration
        self._unit = unit
        self.unit_conversion_flag = False

        self.parent = None

        if concentration and unit:
            self._convert_units()

    @property
    def components(self):
        return [compconc.media_component.name for compconc in self.component_concentrations]

    def __str__(self):
        if self.parent:
            return '+'.join([item for item in
                             [compconc.media_component.name + ' g/L ' + compconc.concentration for compconc in
                              self.component_concentrations] + self.parent_name])
        else:
            return '+'.join([item for item in
                             [compconc.media_component.name + ' g/L '+ str(compconc.concentration) for compconc in
                              self.component_concentrations]])

    @property
    def unique_id(self):
        return self.name

class Environment(Base):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True)
    labware_id = Column(Integer, ForeignKey('labware.id'))
    labware = relationship('Labware')
    shaking_speed = Column(Float)
    shaking_diameter = Column(Float,nullable=True)
    temperature = Column(Float)

    def __init__(self, labware=None):
        self.labware = Labware() if labware is None else labware

    def __str__(self):
        return '%s %sRPM %sC' % (self.labware, self.shaking_speed, self.temperature)

class Labware(Base):
    __tablename__ = 'labware'

    id = Column(Integer, primary_key=True)
    name = Column(String,unique=True)

    def __str__(self):
        return str(self.name)

class Analyte(Base):
    __tablename__ = 'analyte'

    name = Column(String, primary_key=True)
    default_type = Column(String)

class TrialIdentifier(Base):
    """
    Carries information about the run through all the objects

    Attributes
    -----------
    strain.name : str
        Strain name e.g. 'MG1655 del(adh,pta)'
    id_1 : str, optional
        First identifier, plasmid e.g. 'pTrc99a'
    id_2 : str, optional
        Second identifier, inducer e.g. 'IPTG'
    replicate_id : str
        The replicate number, e.g. '1','2','3','4'
    time : float
        The time of the data point, only relevant in :class:`~TimePoint` objects
    analyte_name : str
        The name of the titer, e.g. 'OD600','Lactate','Ethanol','Glucose'
    titerType : str
        The type of titer, three acceptable values e.g. 'biomass','substrate','product'
    """

    __tablename__ = 'trial_identifier'

    id = Column(Integer, primary_key=True)

    strain_id = Column(Integer, ForeignKey('strain.id'))
    strain = relationship("Strain")

    media_name = Column(String, ForeignKey('media.name'))
    media = relationship("Media")

    environment_id = Column(Integer, ForeignKey('environment.id'))
    environment = relationship('Environment')

    # trial specific
    replicate_id = Column(Integer)

    # analyte data specific
    analyte_name = Column(String,ForeignKey('analyte.name'))
    analyte_type = Column(String)

    id_1 = Column(String)
    id_2 = Column(String)
    id_3 = Column(String)

    def __init__(self, strain=None, media=None, environment=None):
        self.strain = Strain() if strain is None else strain
        self.media = Media() if media is None else media
        self.environment = Environment() if strain is None else environment

        self.time = -1
        self.replicate_id = -1
        self.analyte_name = None

    def __str__(self):
        return "strain: %s, media: %s, env: %s, analyte: %s, t: %s h, rep: %s" % (self.strain,self.media,self.environment,self.analyte_name,self.time,self.replicate_id)

    def summary(self, items):
        summary = dict()
        for item in items:
            summary[item] = getattr(self, item)
        return summary

    def parse_identifier(self, id):
        # Split by |
        parameter_values = id.split('|')

        for parameter_value in parameter_values:

            if len(parameter_value.split(':')) == 2:
                key, val = parameter_value.split(':')

                if len(key.split('__')) == 1:
                    if key in ['strain', 'media', 'environment']:
                        getattr(self, key).nickname = val
                    elif key == 'rep':
                        self.replicate_id = int(val)
                    elif key == 'time':
                        self.time = float(val)
                    else:
                        raise Exception('Unknown key' + str(key))
                elif len(key.split('__')) == 2:
                    attr1, attr2 = key.split('__')

                    # Set knockouts
                    if attr1 == 'strain':
                        if attr2 == 'ko':
                            kos = val.split(',')
                            for ko in kos:
                                self.strain.knockouts.append(Knockout(gene=ko))
                        if attr2 == 'plasmid':
                            self.strain.plasmids.append(Plasmid(name=val))

                    # Set component concentrations
                    elif attr1 == 'media':
                        if attr2 == 'cc':
                            conc, comp = val.split(' ')
                            self.media.component_concentrations.append(ComponentConcentration(MediaComponent(comp), conc))
                        elif attr2 == 'base':
                            self.media.base = Media(nickname=val)
                        else:
                            setattr(self.media,attr2,val)


                    elif attr1 == 'environment':
                        if attr2 == 'labware':
                            self.environment.labware.name = val
                        elif attr2 in ['shaking_speed','temperature']:
                            setattr(self.environment,attr2,float(val))
                        else:
                            setattr(self.environment,attr2,val)
                    else:
                        # Set other attrs
                        setattr(getattr(self, attr1), attr2, val)
                else:
                    raise Exception('Too many subparameters traversed' + str(key))
            else:
                raise Exception('Malformed parameter')

    def parse_trial_identifier_from_csv(self, csv_trial_identifier):
        """
        Used to parse a CSV trial_identifier

        Parameters
        ----------
        csv_trial_identifier : str
            a comma-separated string containing a TrialIdentifier in standard form - strain.name,id_1,id_2,replicate_id
        """
        if type(csv_trial_identifier) is str:
            tempParsedIdentifier = csv_trial_identifier.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier, " <-- not processed")
            if len(tempParsedIdentifier) > 0:
                self.strain = Strain(nickname=tempParsedIdentifier[0])
            if len(tempParsedIdentifier) > 1:
                self.id_1 = tempParsedIdentifier[1]
            if len(tempParsedIdentifier) > 2:
                self.id_2 = tempParsedIdentifier[2]
            if len(tempParsedIdentifier) > 3:
                try:
                    self.replicate_id = int(tempParsedIdentifier[3])
                except:
                    print("Couldn't parse replicate_id from ", tempParsedIdentifier)
            if len(tempParsedIdentifier) > 4:
                self.time = float(tempParsedIdentifier[4])

    def unique_analyte_data(self):
        """
        Returns a string identifying the unique attribute of a single trial
        """
        if self.analyte_name:
            an = self.analyte_name
        else:
            an = ''

        return self.unique_single_trial() + ' ' + an

    def unique_single_trial(self):
        """
        Returns a string identifying the unique attribute of a single trial
        """
        return self.unique_replicate_trial() + ' ' + str(self.replicate_id)

    def unique_replicate_trial(self):
        """
        Returns a string identifying the unique attribute of a replicate trial
        """
        return ' '.join([str(getattr(self,attr))
                         for attr in ['strain','media','environment','id_1',
                                      'id_2','id_3']
                         if str(getattr(self,attr) != '') ])

    def get_analyte_data_statistic_identifier(self):
        ti = TrialIdentifier()
        for attr in ['strain','media','environment','id_1','id_2','id_3','analyte_name','analyte_type']:
            setattr(ti,attr,getattr(self,attr))
        return ti

    def get_replicate_trial_trial_identifier(self):
        ti = TrialIdentifier()
        for attr in ['strain','media','environment','id_1','id_2','id_3']:
            setattr(ti,attr,getattr(self,attr))
        return ti