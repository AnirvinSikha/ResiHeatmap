''''
file used solely to update rates.
It's this short because it only uses tone function call from Genability.py
'''

import Genability

def updateRates():
    Genability.update_rates()

def check_zip(z):
    test = Genability.TariffEngine(str("city"), str(1), str(z), "2018-01-01T00:00:00", "2019-01-01T00:00:00")
    print(test.get_utility())

updateRates()
#check_zip(3302)
