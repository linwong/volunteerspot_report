from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import time
import os
import configparser
import csv

class AutoVivification(dict):
  """Implementation of perl's autovivification feature."""
  def __getitem__(self, item):
    try:
      return dict.__getitem__(self, item)
    except KeyError:
      value = self[item] = type(self)()
      return value


class Report(object):
  def __init__(self):
    # Config
    #  ** Check config.ini.sample for configuration options
    config = configparser.ConfigParser()
    config.read('config.ini')
    self.username          = config['DEFAULT']['username']
    self.password          = config['DEFAULT']['password']
    self.save_directory    = config['DEFAULT']['save_directory']
    self.filename          = config['DEFAULT']['filename']
    self.volunteerspot_uri = config['DEFAULT']['volunteerspot_uri']


  def download(self):
    # I don't believe there's an API to download reports from
    # volunteerspot.com.  We use Selenium to login, naviagate to the
    # reports page and click on the export CSV file

    # Start X Framebuffer
    display = Display(visible=0, size=(800,600))
    display.start()
    
    login_uri = 'https://volunteerspot.com/login/signin'

    fp = webdriver.FirefoxProfile()
    fp.set_preference('browser.download.folderList', 2) # custom location
    fp.set_preference('browser.download.manager.showWhenStarting', False)
    fp.set_preference('browser.download.dir', self.save_directory)
    fp.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')

    driver = webdriver.Firefox(fp)
    driver.get(login_uri)

    while True:
      try:
        username_input = driver.find_element_by_id('login-email')
        password_input = driver.find_element_by_id('login-password')
        break
      except:
        print 'where is the element?'
        time.sleep(1)

    username_input.send_keys(self.username)
    password_input.send_keys(self.password)
    password_input.submit()

    # Wait for user to login
    time.sleep(5)

    # Goto reports page
    driver.get(self.volunteerspot_uri)

    # Wait for page to load
    while True:
      try:
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'button.export')))
        export_button = driver.find_element_by_css_selector('button.export')
        time.sleep(1)
        break
      except:
        time.sleep(1)
        print 'waiting for export button'

    print self.filename
    print self.username
    print os.path.exists(self.filename)
    if os.path.exists(self.filename):
      print 'removing file' + self.filename
      os.remove(self.filename)

    # Click on the export button which saves the file
    export_button.click()

    # Quit Firefox once file has been saved
    while True:
      if os.path.isfile(self.filename):
        print 'quitting firefox'
        driver.quit()
        break
      else:
        print 'waiting for download'
        time.sleep(1)

    display.stop()

  def parse_csv(self):
    filename = self.filename
    lines = []
    with open(filename) as file:
      reader = csv.reader(file)
      for row in reader:
        lines.append(row)
    file.close()
    # remove header
    lines.pop(0)

    data = AutoVivification()
    for line in lines:
      print line
      date = line[0]
      role = line[1]
      if len(line) > 6:
        name = line[6]
      else:
        name = None
      data[date][role] = name

    for key in sorted(data):
      print key
      print data[key]


  def email(self):
    print 'email'
