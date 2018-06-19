import json
import matplotlib as plt
import numpy as np
import requests
import os
import Parser



LA = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
ratesEWeek = "RateEweek.csv"

LosAngeles = Parser.fileParse(LA)
rates = Parser.fileParse(ratesEWeek)

