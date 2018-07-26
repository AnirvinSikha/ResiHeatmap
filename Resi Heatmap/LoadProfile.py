'''
Parses LoadProfiles folder.
Performs calculation to determine bill befor solar.
May be deleted after Genability.py is functional
'''
import datetime

def run(load, rates):
    date_time = load.getTotalHour()
    consumption = []
    before_solar = []
    import_rates = []

    totalHour = 0 #total hour goes from 0 - 8759 inclusive

    # Parses load file into 4 outputs: date values, electricity consumption values,
    # bill before solar, and the rates used to calculate
    while totalHour < 8760:
        consumption += [load.getElectricity()[totalHour]]

        month_date = load.convertMonth(load.getTotalHour()[totalHour])
        day_date = load.convertDay(load.getTotalHour()[totalHour])
        date =  datetime.date(2013, month_date, day_date) #the date in 2013
        is_week = "week"
        if date.weekday() >= 5: #5,6 = Saturday, Sunday. 0-4 is Monday-Friday
            is_week = "weekend"

        r_Week = rates.getWeek() == is_week
        r_Month = rates.getMonth() == month_date
        hour = totalHour % 24

        rate_value = rates.getHour(hour)[r_Week & r_Month]
        import_rates += [float(rate_value)]

        before_solar += [float(rate_value * load.getElectricity()[totalHour])]
        totalHour += 1
    return (date_time, consumption, before_solar, import_rates)
