from scipy.integrate import odeint
import numpy as np
import matplotlib.pyplot as plt


def generate_data(y0, t, model, biomass_keys, substrate_keys, product_keys, noise=0, plot=True):
    """
    Generates synthetic data

    Parameters
    ----------
    y0 : list
        Starting values
    t : array
        Time vector
    model: cobraPy model
        Optimized cobraPy model
    biomass_keys: list
        A list with the a string of the biomass name
    substrate_keys: list
        A list with the a string of the susbstrate name
    product_keys: list
        A list of strings of product names
    noise: float, optional
        If you'd like to add some noise to parameters
    plot : bool, optional
        Flag for plotting data

    Returns
    -------
    dFBA_profile: dict
        Returns a dict with time profiles for each product, substrate and biomass
    """""

    sol = model.optimize()

    # Let's assign the data to these variables
    biomass_flux = [sol.x_dict[biomass_keys[0]]]

    substrate_flux = [sol.x_dict[substrate_keys[0]]]

    product_flux = [sol.x_dict[key] for key in product_keys]

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
    sol = odeint(dFBA_functions, y0, t, args=([flux * np.random.uniform(1 - noise, 1 + noise)
                                               for flux in biomass_flux],
                                              [flux * np.random.uniform(1 - noise, 1 + noise)
                                               for flux in substrate_flux],
                                              [flux * np.random.uniform(1 - noise, 1 + noise)
                                               for flux in product_flux]))

    dFBA_profile = {key: [row[i] for row in sol] for i, key in enumerate(exchange_keys)}

    if plot:
        plt.figure(figsize=[12, 6])
        for key in exchange_keys:
            plt.plot(t, dFBA_profile[key])
        plt.legend(exchange_keys, loc=2)

    return dFBA_profile


def dynamic_model_integration(t, y0, model, single_trial, biomass_keys, substrate_keys, product_keys,extra_points_multiplier = 1):
    from scipy.interpolate import interp1d
    import progressbar
    bar = progressbar.ProgressBar()

    def dFBA_functions(y, t, t_max, model, analyte_dict, bar):
        if t <= t_max:
            bar.update(t/t_max*100)

        for analyte in analyte_dict:
            model.reactions.get_by_id(analyte).lower_bound = analyte_dict[analyte](t)
            model.reactions.get_by_id(analyte).upper_bound = analyte_dict[analyte](t)

        solution = model.optimize()

        exchange_keys = biomass_keys + substrate_keys + product_keys

        if solution.status == 'infeasible':
            return [0]*len(exchange_keys)
        else:
            # Let's assign the data to these variables
            biomass_flux = [model.solution.x_dict[biomass_keys[0]]]

            substrate_flux = [model.solution.x_dict[substrate_keys[0]]]

            product_flux = [model.solution.x_dict[key] for key in product_keys]

            exchange_keys = biomass_keys + substrate_keys + product_keys

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


    synthetic_t = np.linspace(0,t[-1],len(t)*extra_points_multiplier)
    # Now let's generate the data
    sol = odeint(dFBA_functions, y0, synthetic_t, args=(t[-1], model,
                                              {analyte: interp1d(t, single_trial.analyte_dict[analyte].specific_productivity,
                                                                 bounds_error=False,
                                                                 fill_value=(single_trial.analyte_dict[
                                                                                 analyte].specific_productivity.data[0],
                                                                             single_trial.analyte_dict[
                                                                                 analyte].specific_productivity.data[-1]))
                                               for analyte in single_trial.analyte_dict},
                                              bar))

    analyte_keys = biomass_keys + substrate_keys + product_keys

    dFBA_profile = {key: [row[i] for row in sol] for i, key in enumerate(analyte_keys)}

    plt.figure(figsize=[12, 6])
    for key in analyte_keys:
        plt.plot(synthetic_t, dFBA_profile[key])
    # plt.ylim([0, 250])
    plt.legend(analyte_keys, loc=2)

def generate_replicate_trial():
    from impact.helpers.synthetic_data import generate_data
    import cobra.test
    import numpy as np

    import impact as impt
    # Let's grab the iJO1366 E. coli model, cobra's test module has a copy
    model = cobra.test.create_test_model("ecoli")

    # Optimize the model after simulating anaerobic conditions, we don't get many products aerobically
    model.reactions.get_by_id('EX_o2_e').lower_bound = 0
    model.reactions.get_by_id('EX_o2_e').upper_bound = 0

    # Optimize the model
    model.optimize()

    # Print a summary of the fluxes
    model.summary()

    biomass_keys = ['Ec_biomass_iJO1366_core_53p95M']
    substrate_keys = ['EX_glc_e']
    product_keys = ['EX_for_e','EX_ac_e','EX_etoh_e','EX_succ_e']

    # The initial conditions (mM) [biomass, substrate, product1, product2, ..., product_n]
    y0 = [0.05, 100, 0, 0, 0, 0]
    t = np.linspace(0,20,1000)

    replicateList = []
    for i in range(4):
        # Let's add some noise to the data to simulate experimental error and generate some more data
        dFBA_profiles = generate_data(y0, t, model, biomass_keys, substrate_keys, product_keys, noise = 0.1, plot = False)
        replicateList.append(dFBA_profiles)

    # import matplotlib.pyplot as plt
    # for i, exchange in enumerate(biomass_keys+substrate_keys+product_keys):
    #     plt.figure(figsize=[12,6])
    #     for replicate in replicateList:
    #         plt.plot(t,replicate[exchange])
    #     plt.legend(['Replicate #'+repNum for repNum in ['1','2','3','4']],loc=2)
    #     plt.title(exchange)

    singleTrialList = []
    for replicate_id, replicate in enumerate(replicateList):
        timeCourseList = []
        for exchange in biomass_keys + substrate_keys + product_keys:
            trial_identifier = impt.ReplicateTrialIdentifier()
            trial_identifier.strain_id = 'iJO1366'
            trial_identifier.id_1 = 'Anaerobic'
            trial_identifier.replicate_id = replicate_id
            if exchange in biomass_keys:
                trial_identifier.analyte_name = exchange
                trial_identifier.analyte_type = 'biomass'
            if exchange in substrate_keys:
                trial_identifier.analyte_name = exchange
                trial_identifier.analyte_type = 'substrate'
            if exchange in product_keys:
                trial_identifier.analyte_name = exchange
                trial_identifier.analyte_type = 'product'

            tempTimeCourse = impt.TimeCourse()
            tempTimeCourse.trial_identifier = trial_identifier
            tempTimeCourse.time_vector = t
            tempTimeCourse.data_vector = replicate[exchange]
            timeCourseList.append(tempTimeCourse)

            # Now we can build a singleTrial object and load all the data
            singleTrial = impt.SingleTrial()
            for timeCourse in timeCourseList:
                singleTrial.add_analyte_data(timeCourse)

        singleTrialList.append(singleTrial)

        replicateTrial = impt.ReplicateTrial()
        for singleTrial in singleTrialList:
            replicateTrial.add_replicate(singleTrial)

        return replicateTrial
