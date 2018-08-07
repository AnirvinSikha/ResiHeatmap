from SavingsPerf import *


# Calculate cost and Savings
total = pd.DataFrame([],columns=['rate','capacity','solarfactor','savingsbasic','savingsimproved','savingsoptimal'])
k=0

# Download data profiles
site = 'Sunpower_Product_Test-Residential_LA-DataFile'
d = open_profiles(site)

# Download Rate
ratename_list = ['E', 'Hawai', 'SCE_current']
capacity_list = [8,9.3,10.5,11.5]
solarfactor_list = [0.75,1,1.25,1.5]

for ratename in ratename_list:
    print("rate running:" + str(ratename))
    d = get_rates(d, ratename)

    for sf in solarfactor_list:
        print('solar factor: ' + str(sf))
        d['solar'] = d['solar0'] * sf

        for capacity in capacity_list:
            print('capacity: ' + str(capacity))

            # if the file doesnt exist create it!
            if os.path.isfile('C:\Users\ctouati\PyCharmProject\EquinoxStorage-/Dispatch_LA_' + str(ratename) + str(
                    capacity) + 'kWh_' + str(sf) + '.csv') == False:
                # Battery spec
                power_rate = 5 # kW
                I = 0.25
                soc = 0 # battery is empty on the 1st of january 00.00
                soc2 = 0
                soc3 = 0
                e = 0.88 # battery efficiency round trip


                #for each line, the dispatch based on the previous soc
                for i in d.index:

                    # BASIC DISPATCH

                    # Create the dispatch column for each line
                    d.loc[i, 'basic storage'] = basic_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'], soc)

                    # update the soc
                    if d.loc[i, 'basic storage'] < 0: # the battery is charging
                        soc = soc - (d.loc[i, 'basic storage'] * I*e**0.5) / capacity  # e^0.5 is one way efficiency
                    else:
                        soc = soc - (d.loc[i, 'basic storage'] * I / e ** 0.5) / capacity
                    d.loc[i, 'soc'] = soc

                    #IMPROVED DISPATCH

                    # Add a column to know whether it is worth charging the solar production
                    if d.loc[i, 'rate_export'] <= e*max(d.loc[i:i+48/I, 'rate']):
                        d.loc[i,'chargesolar'] = 1
                    else:
                        d.loc[i, 'chargesolar'] = 0

                    # Create the improved dispatch
                    d.loc[i, 'improved storage'] = improved_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'], d.loc[i, 'chargesolar'], soc2)

                    # update the soc
                    if d.loc[i, 'improved storage'] < 0: # the battery is charging
                        soc2 = soc2 - (d.loc[i, 'improved storage'] * I*e**0.5) / capacity  # e^0.5 is one way efficiency
                    else:
                        soc2 = soc2 - (d.loc[i, 'improved storage'] * I / e ** 0.5) / capacity
                    d.loc[i, 'soc2'] = soc2
                    # SAVINGS DISPATCH

                    # add a column whether it is worth taking from the grid instead of the battery
                    if d.loc[i, 'rate'] <= e*max(d.loc[i:i+48/I, 'rate']):
                        d.loc[i,'grid'] = 1
                    else:
                        d.loc[i, 'grid'] = 0

                    # Create the improved dispatch
                    d.loc[i, 'savings storage'] = best_dispatch(d.loc[i, 'load'], d.loc[i, 'solar'],
                                                                      d.loc[i, 'chargesolar'], d.loc[i, 'grid'], soc3)
                    # update the soc
                    if d.loc[i, 'savings storage'] < 0: # the battery is charging
                        soc3 = soc3 - (d.loc[i, 'savings storage'] * I*e**0.5) / capacity  # e^0.5 is one way efficiency
                    else:
                        soc3 = soc3 - (d.loc[i, 'savings storage'] * I / e ** 0.5) / capacity
                    d.loc[i, 'soc3'] = soc3


                print('basic and improved dispatch is done')

                # OPTIMAL DISPATCH

                # Find the optimal storage for each week
                for i in range(0,53):
                    #print('working on week' +str(i))
                    optimal_dispatch(d, i)



                # export file
                d.to_csv('Dispatch_LA_' + str(ratename)+ str(capacity) + 'kWh_'+str(sf) + '.csv')

                total.loc[k, 'rate'] = ratename
                total.loc[k, 'capacity'] = capacity
                total.loc[k, 'solarfactor'] = sf
                total.loc[k, 'solar/load'] = d.load.mean() / d.solar.mean()
                total.loc[k, 'savingsbasic'] = savings(d, 'basic')
                total.loc[k, 'savingsimproved'] = savings(d, 'improved')
                total.loc[k, 'savingssavings'] = savings(d, 'savings')
                total.loc[k, 'savingsoptimal'] = savings(d, 'optimal')
                k += 1 # new line for the next one

total['perf basic'] = abs(total['savingsbasic']/total['savingsoptimal'])
total['perf improved'] = abs( total['savingsimproved']/total['savingsoptimal'])
total['perf best'] = abs(total['savingsbest']/total['savingsoptimal'])

total.to_csv('Summary.csv')
print('done results extracted under Summary')



# si ca rate!

ratename_list = ['E', 'Hawai', 'SCE_current']
capacity_list = [8,9.3,10.5,11.5]
solarfactor_list = [0.75,1,1.25,1.5]

total = pd.DataFrame([])
k=0
I=0.25


for ratename in ratename_list:
    print("rate running:" + str(ratename))
    for sf in solarfactor_list:
        print(sf)
        for capacity in capacity_list:
            print(capacity)
            if os.path.isfile('C:\Users\ctouati\PyCharmProject\EquinoxStorage-/Dispatch_LA_' + str(ratename)+ str(capacity) +'kWh_'+str(sf)+ '.csv') == True:
                soc4 = 0
                d = pd.read_csv('C:\Users\ctouati\PyCharmProject\EquinoxStorage-/Dispatch_LA_' + str(ratename)+ str(capacity) +'kWh_'+str(sf)+ '.csv')
                print('d is opened')

                total.loc[k, 'rate'] = ratename
                total.loc[k, 'capacity'] = capacity
                total.loc[k, 'solarfactor'] = sf
                total.loc[k, 'PV bill'] = bill(d,'solar')
                total.loc[k, 'savingsbasic'] = savings(d, 'basic')
                total.loc[k, 'savingsimproved'] = savings(d, 'improved')
                total.loc[k, 'savingssavings'] = savings(d, 'savings')
                total.loc[k, 'savingsbest'] = savings(d, 'best')
                total.loc[k, 'savingsoptimal'] = savings(d, 'optimal')
                k += 1
                print('next file')

for i in total.index:
    if total.loc[i,'perf best'] > total.loc[i,'perf improved']:
        total.loc[i,'better'] = 'yes'
    else:
        total.loc[i, 'better'] = 'no'
