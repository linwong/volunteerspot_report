#!/usr/bin/python

from report import *

# First we need to download the report
report = Report()
report.download()

# Next we parse the data from the csv file
report.parse_csv()

# Finally we email the data
#report.email()
