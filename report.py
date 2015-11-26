from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
import time
import os
import configparser
import csv
import datetime
import json
import smtplib

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
    self.smtp              = config['SMTP']['smtp']
    self.smtp_port         = config['SMTP']['smtp_port']
    self.smtp_username     = config['SMTP']['smtp_username']
    self.smtp_password     = config['SMTP']['smtp_password']
    self.email_template    = config['REPORT']['email_template']
    self.email_from        = config['REPORT']['from']
    self.email_subject     = config['REPORT']['subject']
    self.emails            = json.loads(config['REPORT']['emails'])

    
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

    if os.path.exists(self.filename):
      os.remove(self.filename)

    # Click on the export button which saves the file
    export_button.click()

    # Quit Firefox once file has been saved
    while True:
      if os.path.isfile(self.filename):
        driver.quit()
        break
      else:
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

    self.data = AutoVivification()
    for line in lines:
      date = line[0]
      role = line[1]
      if len(line) > 6:
        name = line[6]
      else:
        name = None
      self.data[date][role] = name



  def get_next_dates(self, number, day):
    current_day = datetime.date.today()
    self.dates = []
    while (number > 0):
      target_day = current_day + datetime.timedelta( (day - 1 - current_day.weekday()) % 7 + 1 )
      self.dates.append(target_day.isoformat())
      current_day = target_day
      number -= 1
      

  # -------THIS IS HARD CODED FOR NOW. NEED TO CHANGE-----------
  def send_email(self):
    with open(self.email_template + '.txt') as file:
      body = file.read()
    file.close()
    with open(self.email_template + '.html') as file:
      html = file.read()
    file.close()

    # Processing data
    # Check if anybody signed up for this coming Sunday
    if (not self.data[self.dates[0]]['Worship Leader']):
      # we need someone
      need_text = 'NOTE: There is NO Worship Leader signed up for this Sunday, ' + self.dates[0]
    else:
      need_text = ''
    body = body.replace('__NEED__', need_text)
    html = html.replace('__NEED__', need_text)

    table = '<table>'
    for date in self.dates:
      data = self.data[date]
      table += '<tr>'
      table += '<td>'+date+'</td>'
      table += '<td>Worship Leader: ' + (data['Worship Leader'] or 'None') + '</td>'
      table += '</tr>'
    table += '</table>'

    body = body.replace('__SIGNUPS__', table)
    html = html.replace('__SIGNUPS__', table)
        
    FROM = self.email_from
    TO = self.emails
    SUBJECT = self.email_subject + ' - ' + datetime.date.today().isoformat()

    # Prepare actual message
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    msg['To'] = ",".join(TO)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(body, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    try:
      server = smtplib.SMTP(self.smtp+':'+self.smtp_port)
      server.ehlo()
      server.starttls()
      server.login(self.smtp_username, self.smtp_password)
      server.sendmail(FROM, TO, msg.as_string())
      server.close()
    except Exception, error:
      print error
