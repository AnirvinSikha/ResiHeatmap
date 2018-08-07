import pandas as pd
import time
from pyomo.environ import *
import numpy as np
import os



def open_profiles(name):
    # Download data site
    d = pd.read_csv(str(name) + '.csv', skiprows=48)
    #d = pd.read_csv('/Users/coralietouati/PyCharmProjects/EquinoxStorage-/' + str(name) + '.csv', skiprows=48)
    # delete empty columns
    d.dropna(how = 'all', axis='columns', inplace=True)
    # delete empty lines
    d.dropna(inplace = True)
    # Create a full date column (day and hour)
    d['date'] = pd.to_datetime(d['Date'] + ' ' + d['Time'], format='%m/%d/%Y %H:%M')
    d.drop(['Date','Time',' ', 'net load'], axis=1, inplace=True)
    d['net load solar'] = d['load'] - d['solar']
    #add hour and month column
    d['month'] = pd.DatetimeIndex(d['date']).month
    d['week'] = pd.DatetimeIndex(d['date']).week
    d['hour'] = pd.DatetimeIndex(d['date']).hour
    d['day'] = pd.DatetimeIndex(d['date']).dayofweek
    d.loc[ (d['week'] == 52) & (d['month'] == 1 ), 'week'] = 0
    # Reorder columns
    d = d[['date', 'month', 'week', 'day', 'hour', 'load', 'solar','batteryetb']]
    d['solar0'] = d['solar']

    return d


def get_rates(d,ratename):
    rate_week = pd.read_csv('C:/Users/ctouati/PyCharmProject/EquinoxStorage-/Rates/Rate' + str(ratename) + '_week.csv',
                            index_col='month', header=0)
    rate_weekend = pd.read_csv(
        'C:/Users/ctouati/PyCharmProject/EquinoxStorage-/Rates/Rate' + str(ratename) + '_weekend.csv',
        index_col='month', header=0)
    # rate_week = pd.read_csv('/Users/coralietouati/PyCharmProjects/EquinoxStorage-/Rate' + str(ratename) + 'week.csv',index_col='month', header=0)
    # rate_weekend = pd.read_csv('/Users/coralietouati/PyCharmProjects/EquinoxStorage-/Rate' + str(ratename) + 'weekend.csv',index_col='month', header=0)
    for i in d.index:
        # add import rates
        if d.loc[i, 'date'].weekday() <= 4:
            d.loc[i, 'rate'] = rate_week.iloc[int(d.loc[i, 'month']) - 1, int(d.loc[i, 'hour'])]
        else:
            d.loc[i, 'rate'] = rate_weekend.iloc[int(d.loc[i, 'month']) - 1, int(d.loc[i, 'hour'])]
        # add export rates
        if ratename == 'Hawai':
            d.loc[i, 'rate_export'] = 0
        else:
            d.loc[i, 'rate_export'] = d.loc[i, 'rate'] - 0.02
    return d

def add_chargesolar(d, rate, e=0.88, I=1):
    for i in d.index:
        if d.loc[i, 'rate_export'] <= e * max(d.loc[i:i + 12*I, 'rate']):
            d.loc[i, str(rate) + 'chargesolar'] = 1
        else:
            d.loc[i,  str(rate) + 'chargesolar'] = 0


def add_grid(d, rate, e=0.88, I=1):
    for i in d.index:
        if d.loc[i, 'rate'] <= e * max(d.loc[i:i + 12* I, 'rate']):
            d.loc[i, str(rate) + 'grid'] = 1
        else:
            d.loc[i, str(rate) + 'grid'] = 0


def add_highsolar(d, customer, I=1):
    for i in d.index:
        if d.loc[i:i + 24*I, 'solar'].sum() / d.loc[i:i + 24 * I, 'load'].sum() > 1: # looking at the future for testing only. AFTER CHANGE TO -12*I
            d.loc[i, str(customer) + 'highsolar'] = 1
        else:
            d.loc[i,  str(customer) + 'highsolar'] = 0




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




def basic_dispatch(load, solar, soc, capacity):
    """" SELF CONSUMPTION - Return a basic dispatch: Charge when there is extra solar and discharge when needed"""
    soc_min = 0 # need to change getpower if change the value
    storage = get_power(load-solar, soc, soc_min, capacity=capacity)
    return storage


def improved_dispatch(load,solar,chargesolar,grid,soc, capacity):
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




def best_dispatch(load,solar,chargesolar,grid,highsolar,soc,capacity):
    """" Based on the basic dispatch but will only charge if it is worth it: if it is off peak and if
    the TOU difference compensate the energy losses"""

    soc_min = 0

    # if it is worth charging solar (ie: high export rate)
    if chargesolar == 1:
        if grid == 1 and highsolar == 0: # if it is worth taking from the grid (ie: low import rate)
           # if there is space in the battery charge solar and use the grid to meet the load
            storage = get_power(-solar, soc, soc_min, capacity=capacity)

        else: # otherwise take from the battery (ie: high import rate)
            storage = get_power(load-solar, soc, soc_min, capacity=capacity)

    else: # export solar
        if grid == 1 and highsolar == 0:
            storage = 0
        else:
            storage = get_power(load, soc, soc_min, capacity=capacity)

    return storage


def optimal_dispatch(d,week,customer="", ratename = "", power_rate=5, e =0.88, I=1, capacity=9.3):


        # Initialisation
    if week == 'all':
        load = d.load
        solar = d.solar
        rate = d.rate
        rate_exp = d.rate_export
        index = load.index
    else:
        load = d.load[d.week == week]
        solar = d.solar[d.week == week]
        rate = d.rate[d.week == week]
        rate_exp = d.rate_export[d.week == week]
        index = load.index


        # CREATE MODEL
    m = ConcreteModel()

        # VARIABLES
    # Charge kW in the battery from PV
    m.charge = Var(range(int(index.min()),int(index.max())+1),within = NonNegativeReals )
    # Charge kW in the battery from the grid
    m.charge_grid = Var(range(int(index.min()),int(index.max())+1), within = NonNegativeReals )
    # Import from grid to load for consumption
    m.imp = Var(range(int(index.min()),int(index.max())+1), within=NonNegativeReals)
    # Discharge kW to the load from the battery
    m.discharge = Var(range(int(index.min()),int(index.max())+1), bounds=(0, power_rate))
    # Amount exported from Pv to the grid kW (battery cannot export)
    m.export = Var(range(int(index.min()),int(index.max())+1), within = NonNegativeReals)
    # Use PV energy to meet load demand
    m.pv_load = Var(range(int(index.min()),int(index.max())+1), within=NonNegativeReals)
    # kWh in the battery at each iteration
    m.x = Var(range(int(index.min()),int(index.max())+1), bounds=(0, capacity))



        # OBJECTIV FONCTION: minimizes energy charge (import - export)
    m.value = Objective( expr= sum( (m.charge_grid[i] + m.imp[i])*rate[i]*I -
                                    m.export[i]*rate_exp[i]*I for i in range(int(index.min()), int(index.max())+1)), sense = minimize)

       # CONSTRAINTS
    # Respect solar production
    def solar_rule(m, i):
        return m.pv_load[i] + m.export[i] + m.charge[i] == solar[i]
    m.solar = Constraint(RangeSet(int(index.min()), int(index.max())), rule=solar_rule)

    # Meet the load demand
    def loads_rule(m, i):
        return m.pv_load[i] + m.discharge[i] + m.imp[i] == load[i]
    m.loads = Constraint(RangeSet(int(index.min()), int(index.max())), rule=loads_rule)

    # charge not faster that C rate
    def charging_rule(m, i):
        return m.charge[i] + m.charge_grid[i] <= power_rate
    m.charging = Constraint(RangeSet(int(index.min()), int(index.max())), rule= charging_rule)

    # FOr ITC, cant charge from solar
    def solar_charging_rule(m, i):
        return m.charge_grid[i] == 0
    m.solarcharging = Constraint(RangeSet(int(index.min()), int(index.max())), rule=solar_charging_rule)

    # energy in the bat must be positive and lesser than capacity
    def bat_rule(m, i):
        return m.x[i] == sum(m.charge[t]*e**0.5 + m.charge_grid[t]*e**0.5 - m.discharge[t]/e**0.5 for t in range(int(index.min()), i+1))*I
    m.bat = Constraint(RangeSet(int(index.min()), int(index.max())), rule = bat_rule)

    # SOLVE
    #solver = SolverFactory('cbc', executable='./COIN-OR-1.7.3-macosx-x86_64-clang500.2.76/bin/cbc')
    solver = SolverFactory('cbc', executable='./cbc')
    status = solver.solve(m)
    # Print the status of the solved LP
    #print("Status = %s" % status.solver.termination_condition)

    # store results
    for i in range(int(index.min()), int(index.max())+1):
        d.loc[i, str(customer) + str(ratename) + 'optimal storage'] = - value(m.charge[i]) - value(m.charge_grid[i]) + value(m.discharge[i])


def full_dispatch(d,algo, customer, rate, e,I,capacity=9.3):

    if algo == 'all':
        full_dispatch(d, 'basic', customer, rate, e, I, capacity)
        full_dispatch(d, 'improved', customer, rate, e, I, capacity)
        full_dispatch(d, 'best', customer, rate, e, I, capacity)
        full_dispatch(d, 'optimal', customer, rate, e, I, capacity)

    elif algo == 'basic':
        soc = 0
        for i in d.index:
            storage = basic_dispatch(d.load[i], d.solar[i], soc , capacity=capacity)
            d.loc[i, str(customer) + str(rate) + str(algo) + ' storage'] = storage
            soc = update_soc(storage, soc, e, I, capacity=capacity)


    elif algo == 'improved':
        soc = 0
        for i in d.index:
            storage = improved_dispatch(d.load[i], d.solar[i], d.loc[i,str(rate) + 'chargesolar'], d.loc[i,str(rate) + 'grid'], soc, capacity=capacity)
            d.loc[i, str(customer) + str(rate) + str(algo) + ' storage'] = storage
            soc = update_soc(storage, soc, e, I, capacity=capacity)
    elif algo == 'best':
        soc = 0
        for i in d.index:
            storage = best_dispatch(d.load[i], d.solar[i], d.loc[i,str(rate) + 'chargesolar'], d.loc[i,str(rate) + 'grid'], d.loc[i,str(customer) + 'highsolar'], soc, capacity=capacity)
            d.loc[i, str(customer) + str(rate) + str(algo) + ' storage'] = storage
            soc = update_soc(storage, soc, e, I, capacity=capacity)

    elif algo == 'optimal':
            optimal_dispatch(d, 'all', customer, rate, capacity=capacity)

    else:
        print('This algorithm does not exist')


def bill(d,algo,I=1):
    """ Return the utility bill. to get the bill with solar only put algo = solar"""
    if algo == 'solar':
        netload = d['load'] - d['solar']
    else:
        netload = d['load'] - d['solar'] - d[str(algo) + ' storage']

    #imports = (d[(d['net load'] > 0)]['net load']*d[(d['net load']) > 0]['rate']).sum()
    imports = ((netload>0)* netload * d['rate']).sum()
    exports = -((netload<0)* netload * d['rate_export']).sum()
    return (imports - exports)*I


def savings(d,algo,I=1):
    """" Returns the savings comapred to pv only"""
    return bill(d,'solar',I) - bill(d,algo,I)
