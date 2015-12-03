#!/usr/bin/python

from report import *
import calendar
import sys
import getopt
from pprint import pprint

try:
    opts, args = getopt.getopt(sys.argv[1:], 'c:p:', ['config=', 'path='])
except getopt.GetoptError:
    sys.exit(2)

config = None
path = ''
for opt, arg in opts:
  if opt in ('-c', '--config'):
    config = arg
  if opt in ('-p', '--path'):
    path = arg

# First we need to download the report
report = Report(path, config)
report.download()

# Next we parse the data from the csv file
report.parse_csv()

# Retrieve next 4 Sundays
report.get_next_dates(4, calendar.SUNDAY)

# Finally we email the data
report.send_email()
