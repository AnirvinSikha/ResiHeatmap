import pandas as pd


# Battery spec
power_rate = 5 # kW
capacity = 9.3 # kWh




def basic_dispatch(load,solar,soc):
    """" Return a basic dispatch: Charge when there is extra solar and discharge when needed
    at a given time the soc of the battery and the expected PV production 'solar' and load profile 'loaad' are the input """

    soc_min = 0.1

    # if the load is higher than solar, then the battery discharges only if there is enough electricity if the battery
    if load > solar:
        if soc > soc_min:
            # Battery is discharging to meet the load, but cannot discharge more than the power rate
            if load - solar <= power_rate:
                storage = load - solar
            else:
                storage = power_rate
        else:
            # there is not enough electricity in the battery --> import from the grid to meet the load
            storage = 0

    # if there is an excess of solar, charge the excess as long as the battery is not full
    else:
        if soc < 1:
            # Battery is charging the excess of solar, but cannot charge more than the power rate
            if load - solar >= - power_rate:
                storage = load - solar
            else:
                storage = - power_rate
        else:
            # if the battery is full, the excess of PV is exported
            storage = 0

    return storage



def full_basic_dispatch(d,I):
    """return d with the dispatch for the entire dataset, the column is called basic storage
        d is the dataframe with load, pv profiles
        I is the data time interval. For an hourly profile I = 1, for a 15 minute data profile I=0.25
    """
    soc = 0
    for i in d.index:
        # Create the dispatch column for each line
        d.loc[i, 'basic storage'] = basic_dispatch(d.loc[i, 'Load'], d.loc[i, 'Solar'], soc)
        # update the soc
        e = 1
        soc = soc - (d.loc[i, 'basic storage'] * I * e ** 0.5) / capacity  # e^0.5 is one way efficiency
        d.loc[i, 'soc'] = soc
    return d
