'''
Parses LoadProfiles folder.
Performs calculation to determine bill befor solar.
May be deleted after Genability.py is functional
'''
def run(load, rates): #load profile file parsed, rates is a pd data frame of import and export rates
    date_time = load.getTotalHour()
    consumption = []
    before_solar = []
    export_rates = rates["Export Rates"].tolist()
    import_rates = rates["Import Rates"].tolist()


    totalHour = 0 #total hour goes from 0 - 8759 inclusive

    # Parses load file into 4 outputs: date values, electricity consumption values,
    # bill before solar, and the rates used to calculate
    while totalHour < 8760:
        consumption += [load.getElectricity()[totalHour]]
        rate_value = import_rates[totalHour]
        before_solar += [float(rate_value * load.getElectricity()[totalHour])]
        totalHour += 1
    return (date_time, consumption, before_solar, import_rates, export_rates)

def incrementation(val, unique):
    val += 1
    if val not in unique:
        return val
    else:
        return incrementation(val, unique)

def getMinimumUniqueSum(arr):
    unique = []
    total = 0
    for i in arr:
        curr = i
        if curr in unique:
            curr = incrementation(curr, unique)
        unique += [curr]
        total += curr
    return total



arr = [5,5,5]
print getMinimumUniqueSum(arr)
