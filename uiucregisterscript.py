import re
import time
import sys
import os

import mechanize
import urllib2
from copy import deepcopy

from lib.BeautifulSoup import BeautifulSoup
from lib.Text4Free import Text4Free
	
#
# Main script
#

CONFIG_FILE = 'config.py'
LOG_FILE = sys.argv[0] + '.log'
CONFIG_PARMS = ["R_SUBJECT", "R_COURSE", "R_SECTIONS_DESIRED", "R_USERNAME", "R_PASSWORD", "R_PHONENUMBER", "R_CARRIER"]
NEEDS_CONFIG = False

# Check if we need to configure.

if len(sys.argv) > 1 and sys.argv[1] == 'config':
    NEEDS_CONFIG = True
else: 
    try:
        f = open(CONFIG_FILE, 'r')
        conts = f.read()
        
        # Check if all config options are there
        for parm in CONFIG_PARMS:
            if re.search('^' + parm, conts, re.M) is None:
                NEEDS_CONFIG = True
                break
    except IOError:
        NEEDS_CONFIG = True
    
# Configure if need be

if NEEDS_CONFIG:
    print "TODO: configuration routine. For now please manually configure " + CONFIG_FILE
    sys.exit()
    
from config import *

# Navigate to the proper page

br = mechanize.Browser()
br.set_handle_robots(False)
br.open("https://apps.uillinois.edu/selfservice/")
br.follow_link(text_regex=r".*(URBANA).*", nr=0)
br.select_form(name="easForm")
br["inputEnterpriseId"] = R_USERNAME
br["password"] = R_PASSWORD
br.submit()
br.follow_link(text_regex=r"Registration & Records", nr=0)
br.follow_link(text_regex=r"Registration", nr=1)
br.follow_link(text_regex=r"Add/Drop Classes", nr=0)
br.follow_link(text_regex=r"I Agree.*", nr=0)
br.select_form(nr=1)
br.submit()
br.select_form(nr=1)
req = br.click(type="submit", nr=1)
br.open(req)
br.select_form(nr=1)
br.find_control(name="sel_subj", nr=1).value = [R_SUBJECT]
br["sel_crse"] = R_COURSE
response = br.submit()
pageSoup = BeautifulSoup(response.read())

# Scrape information from pageText

tableHeads = []
tableData = []

for row in pageSoup.find('table', {'class': "datadisplaytable"}).findAll('tr'):
    if len(row.findAll('th')) > 1 and not tableHeads:
        # This is a header row
        for elem in row.findAll('th'):
            tableHeads.append(re.sub(r'<.*?>', '', str(elem)))
    else:
        # This is a content row
        ct = []
        for elem in row.findAll('td'):
            ct.append(re.sub(r'<.*?>', '', str(elem)))
        tableData.append(ct)
        
idxSection = tableHeads.index('Sec')
idxRem = tableHeads.index('Rem')

sectionsFree = False

for tableRow in tableData:
    if len(tableRow) < max(idxSection, idxRem):
        continue
        
    if tableRow[idxSection] in R_SECTIONS_DESIRED or not R_SECTIONS_DESIRED:
        if int(tableRow[idxRem]) > 0:
            sectionsFree = True
            
# Open the logfile
logfile = open(LOG_FILE, 'a')
logfile.write('Log opened ' + time.strftime("%c") + ' - ')

if sectionsFree:
	# Yes, an opening was found. Text my cell right now!!
    Text4Free.send_text("There is an opening for the class you wanted (" + R_SUBJECT + R_COURSE + ")! Hurry to UIUC enterprise now!", R_PHONENUMBER, R_CARRIER)	
    logfile.write('opening found.\n')
else:
    logfile.write('no slots available.\n')
	
logfile.close()
