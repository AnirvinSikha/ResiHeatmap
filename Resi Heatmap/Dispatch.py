import pandas as pd
import numpy as np

# Battery spec
power_rate = 5 # kW

capacity = 9.3 # kWh
I = 1




# Add criterias
def add_chargesolar(d, e=0.88, I=1):
    for i in d.index:
        if d.loc[i, 'rate_export'] <= e * max(d.loc[i:i + 12*I, 'rate']):
            d.loc[i,'chargesolar'] = 1
        else:
            d.loc[i, 'chargesolar'] = 0


def add_grid(d, e=0.88, I=1):
    for i in d.index:
        if d.loc[i, 'rate'] <= e * max(d.loc[i:i + 12* I, 'rate']):
            d.loc[i, 'grid'] = 1
        else:
            d.loc[i, 'grid'] = 0


def add_highsolar(d, I=1):
    for i in d.index:
        if d.loc[i:i - 24*I, 'solar'].sum() / d.loc[i:i - 24 * I, 'load'].sum() > 1:
            d.loc[i, 'highsolar'] = 1
        else:
            d.loc[i,  'highsolar'] = 0


def update_soc(storage, soc, e=0.88, I=1, capacity=9.3):
    # update the soc
    if storage < 0:  # the battery is charging
        soc = soc - (storage * I * e ** 0.5) / capacity  # e^0.5 is one way efficiency
    else:
        soc = soc - (storage * I / e ** 0.5) / capacity
    return soc


def get_power(storage, soc ,soc_min, e=0.88, I=1, capacity=9.3, max_power_rate = 5):
    """check if the battery has enough energy or if it is not full. Also check if the charge/discharge respect the mx power rate"""
    # First check if the power rate is respected
    if abs(storage) >= max_power_rate:
        storage = np.sign(storage) * max_power_rate

    expected_soc = update_soc(storage, soc, e, I, capacity)
    if storage < 0:
        # if the battery is charging, we need to check there is enough space in the battery
        if expected_soc <= 1:
            return storage
        else:
            return -(1-soc)*capacity/(e**0.5) # max energy we can add in the battery

    else:
        # if it is discharging, we need to check there is enough energy in the battery
        if expected_soc >= soc_min:
            return storage
        else:
            return (soc-soc_min)*capacity*e**0.5



# Dispatch for one datapoint
def self_dispatch(load, solar, soc, capacity):
    """" SELF CONSUMPTION - Return a basic dispatch: Charge when there is extra solar and discharge when needed"""
    soc_min = 0 # need to change getpower if change the value
    storage = get_power(load-solar, soc, soc_min, capacity=capacity)
    return storage


def savings_dispatch(load,solar,chargesolar,grid,soc, capacity):
    """" Based on the basic dispatch but will only charge if it is worth it: if it is off peak and if
    the TOU difference compensate the energy losses"""

    soc_min = 0

    # if it is worth charging solar (ie: high export rate)
    if chargesolar == 1:
        if grid == 1: # if it is worth taking from the grid (ie: low import rate)
           # if there is space in the battery charge solar and use the grid to meet the load
            storage = get_power(-solar, soc, soc_min, capacity=capacity)

        else: # otherwise take from the battery (ie: high import rate)
            storage = get_power(load-solar, soc, soc_min, capacity=capacity)

    else: # export solar
        if grid == 1:
            storage = 0
        else:
            storage = get_power(load, soc, soc_min, capacity=capacity)

    return storage


# DIspatch for the full dataset



def full_savings_dispatch(d,I,e=0.88,capacity = 9.3):

    """return d with the dispatch for the entire dataset, the column is called basic storage
        d is the dataframe with load, pv profiles
        I is the data time interval. For an hourly profile I = 1, for a 15 minute data profile I=0.25
    """
    soc = 0
    for i in d.index:
        # Create the dispatch column for each line

        d.loc[i, 'basic storage'] = savings_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'], soc)

        # update the soc
        e = 0.88
        soc = soc - ((d.loc[i, 'basic storage'] * I * e ** 0.5) / capacity) # e^0.5 is one way efficiency
        d.loc[i, 'soc'] = soc
    return d
