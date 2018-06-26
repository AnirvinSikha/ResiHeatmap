import pandas as pd
import time
from pyomo.environ import *



def open_profiles(name):
    # Download data site
    d = pd.read_csv('C:\Users\ctouati\PyCharmProject\Resi/' + str(name) + '.csv', skiprows=48)
    #d = pd.read_csv('/Users/coralietouati/PyCharmProjects/EquinoxStorage-/' + str(name) + '.csv', skiprows=48)
    # delete empty columns
    d.dropna(how = 'all', axis='columns', inplace=True)
    # delete empty lines
    d.dropna(inplace=True)
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
        if ratename != 'Hawai':
            d.loc[i, 'rate_export'] = 0
        else:
            d.loc[i, 'rate_export'] = d.loc[i, 'rate'] - 0.02
    return d


def basic_dispatch(load,solar,soc):
    """" Return a basic dispatch: Charge when there is extra solar and discharge when needed"""

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


def improved_dispatch(load,solar,chargesolar,soc):
    """" Based on the basic dispatch but will only charge if it is worth it: if it is off peak and if
    the TOU difference compensate the energy losses"""

    soc_min = 0.1

    # if the load is higher than solar, then the battery discharges only if there is enough electricity if the battery
    if load > solar:
        if soc > soc_min:
            # if is on peak and not worth charging, then export all solar and use the battery to meet the load and grid if needed
            if chargesolar == 0:
                if load <= power_rate:
                    storage = load
                else:
                    storage = power_rate
            else:
                # Otherwise, it is off peak battery is discharging to meet the load, but cannot discharge faster than at the power rate
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
            # if it is off peak hour and worth charging, then the excess of solar is charged
            if chargesolar == 1:
                # Battery is charging the excess of solar, but cannot charge faster than at the power rate
                if load - solar >= - power_rate:
                    storage = load - solar
                else:
                    storage = - power_rate
            # if it is not worth charging as it is on peak, the pv excess is exported and nothing is charged
            else:
                storage = 0

        else:
            # if the battery is full, the excess of PV is exported
            storage = 0

    return storage


def optimal_dispatch(d,week):


        # Initialisation
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
        return m.x[i] == sum(m.charge[t]*e + m.charge_grid[t]*e- m.discharge[t] for t in range(int(index.min()), i+1))*I
    m.bat = Constraint(RangeSet(int(index.min()), int(index.max())), rule= bat_rule )



    # SOLVE
    #solver = SolverFactory('cbc', executable='./COIN-OR-1.7.3-macosx-x86_64-clang500.2.76/bin/cbc')
    solver = SolverFactory('cbc', executable='./cbc')
    status = solver.solve(m)
    # Print the status of the solved LP
    #print("Status = %s" % status.solver.termination_condition)

    # store results
    for i in range(int(index.min()), int(index.max())+1):
        d.loc[i, 'charge'] = value(m.charge[i])
        d.loc[i, 'charge_grid'] = value(m.charge_grid[i])
        d.loc[i, 'discharge'] = value(m.discharge[i])


# Calculate cost and Savings
total = pd.DataFrame([],columns=['rate','capacity','solarfactor','savingsbasic','savingsimproved','savingsoptimal'])
i=0



def savings(d,algo):
    bill = (d['load'] * d['rate']).sum() * 0.25
    PVbill = ((d['load'] - d['solar']) * d['rate']).sum() * 0.25
    ESSbill = ((d['load'] - d['solar'] - d[str(algo) + ' storage']) * d['rate']).sum() * 0.25
    return PVbill - ESSbill




# Download data profiles
site = 'Sunpower_Product_Test-Residential_LA-DataFile'
d = open_profiles(site)

# Download Rate
ratename_list = ['E', 'Hawai', 'SCE_current']
capacity_list = [8,9.3,10.5,11.5]
solarfactor_list = [0.9,1,1,1.25,1.5]



for ratename in ratename_list:
    print("rate running:" + str(ratename))

    d = get_rates(d,ratename)

    for sf in solarfactor_list:
        print('solar factor: ' + str(sf))
        d['solar'] = d['solar0'] * sf

        for cap in capacity_list:
            print('capacity: ' + str(cap))
            # Battery spec
            power_rate = 5 # kW
            capacity = cap # kWh
            I = 0.25
            soc = 0 # battery is empty on the 1st of january 00.00
            soc2=0
            e = 0.88 # battery efficiency round trip


            #for each line, the dispatch based on the previous soc
            for i in d.index:
                # BASIC DISPATCH

                # Create the dispatch column for each line
                d.loc[i, 'basic storage'] = basic_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'], soc)

                # update the soc
                soc = soc - (d.loc[i, 'basic storage'] * I*e**0.5) / capacity  # e^0.5 is one way efficiency
                d.loc[i, 'soc'] = soc

                #IMPROVED DISPATCH

                # Add a column to know whether it is work charging the solar production and use the grid to meet the load
                if d.loc[i, 'rate'] <= e* max(d.loc[i:i+48/I, 'rate_export']):
                    d.loc[i,'chargesolar'] = 1
                else :
                    d.loc[i, 'chargesolar'] = 0

                # Create the improved dispatch
                d.loc[i, 'improved storage'] = improved_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'], d.loc[i, 'chargesolar'], soc2)

                # update the soc
                soc2 = soc2 - (d.loc[i, 'improved storage'] * I*e**0.5) / capacity  # e^0.5 is one way efficiency
                d.loc[i, 'soc2'] = soc2


            print('basic and improved dispatch is done')

            # OPTIMAL DISPATCH

            # Find the optimal storage for each week
            for i in range(0,53):
                #print('working on week' +str(i))
                optimal_dispatch(d, i)
            d['optimal storage'] = d['discharge'] - d['charge'] - d['charge_grid']


            # export file
            d.to_csv('Dispatch_LA_' + str(ratename)+ str(capacity) +'kW_'+str(sf)+ '.csv')


            total = pd.DataFrame([], columns=['rate', 'capacity', 'solarfactor', 'savingsbasic', 'savingsimproved',
                                              'savingsoptimal'])
            total.loc[i,'rate'] = ratename
            total.loc[i, 'capacity'] = capacity
            total.loc[i, 'solarfactor'] = sf
            total.loc[i, 'savingsbasic'] = savings(d, 'basic')
            total.loc[i, 'savingsimproved'] = savings(d, 'improved')
            total.loc[i, 'savingsoptimal'] = savings(d, 'optimal')
            i = i+1 # new line for the next one


total['perf basic'] = total['savingsbasic']/total['savingsoptimal']
total['perf improved'] = total['savingsimproved']/total['savingsoptimal']

total.to_csv('Summary.csv')
print('done results extracted under Summary')



