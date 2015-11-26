#!/usr/bin/python

from report import *
import calendar

# First we need to download the report
report = Report()
report.download()

# Next we parse the data from the csv file
report.parse_csv()

# Retrieve next 4 Sundays
report.get_next_dates(4, calendar.SUNDAY)

# Finally we email the data
report.send_email()
