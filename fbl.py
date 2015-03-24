#!/usr/bin/python
# -*- coding: utf8 -*-

"""
fbl.py - Simple script to handle ISP's feedback loops emails 
(when they forward you all emails on which users clicked 'Report as Spam').
Working as a IMAP Client with SSL/TLS.
Also possible run query to mysql database, for example auto unsubscribe users.

Copyright © 2015 Denis Khabarov aka 'Saymon21' & BrandyMint LLC
E-Mail: admin@saymon21-root.pro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Links to setup FeedBack Loops Reports:

 * Yandex: http://yandexfbl.senderscore.net/
 * Mail.ru: https://postmaster.mail.ru/settings/

Example configuration file:

---
debug: False
imap:
  server: imap.example.com
  port: 993
  login: fbl@example.com
  password: secret
  timeout: 10
  debug_level: 4
  folder: FeedBack Loop

database:
  host: db.example.com
  port: 3306
  username: username
  database: databasename
  password: secret

sql:
  unsubscribe_queries:
   - UPDATE users SET notifications=0 WHERE email='{EMAIL}'
"""


import imaplib
import syslog
import yaml
import sys
import signal
import MySQLdb
from socket import setdefaulttimeout
from email.parser import Parser
from os import stat
from stat import ST_MODE
from os.path import isfile
from ssl import SSLError

def is_abuse(msg):
  if msg.get('Content-Type').endswith('message/feedback-report'):
    return True

def validateEmail(address):
  import re
  pattern = "[\.\w]{2,}[@]\w+[.]\w+"
  if re.match(pattern, address):
    return True
  else:
    return False

def sigint_handler(signal, frame):
  print('\nYou pressed Ctrl+C!')
  sys.exit(0)

def main():
  config = None
  try:
    sys.argv[1]
  except IndexError:
    print('usage %s /path/to/fbl.conf.yml' % sys.argv[0])
    sys.exit(1)
  if not isfile(sys.argv[1]):
    print('%s: No such file or directory' % sys.argv[1])
    sys.exit(1)
  if int(oct(stat(sys.argv[1])[ST_MODE])[-3:]) != 600:
    print('%s must not be accessible by others. Use \'chmod 600 fbl.conf.yml\'' % sys.argv[1])
    sys.exit(1)
  try:
    with open(sys.argv[1]) as stream:
      try:
        config = yaml.load(stream)
      except yaml.YAMLError, e:
        syslog.syslog(e)
        sys.exit(1)
  except IOError, e:
    print(e)
    syslog.syslog(e)
    sys.exit(1)
  dbcon = MySQLdb.connect(
    config.get('database').get('host'),
    config.get('database').get('username'),
    config.get('database').get('password'),
    config.get('database').get('database'))
  dbcur = dbcon.cursor()
  setdefaulttimeout(config.get('imap').get('timeout'))
  if config.has_key('debug') and config.get('debug') and config.get('imap').has_key('debug_level'):
    imaplib.Debug = config.get('imap').get('debug_level')
  try:
    imapclient = imaplib.IMAP4_SSL(config.get('imap').get('server'), config.get('imap').get('port'))
  except (imaplib.IMAP4.error,SSLError), e:
    if 'message' in dir(e):
      syslog.syslog(e.message)
    else:
      syslog.syslog(e)
    sys.exit(1)
  imapclient.login(config.get('imap').get('login'), str(config.get('imap').get('password')))
  imapclient.select(config.get('imap').get('folder').replace(' ', '&AKA-'))
  rv,data= imapclient.search(None, "(UNSEEN)")
  if rv == "OK":
    for msg_id in data[0].split(' '):
      if msg_id:
        if config.get('debug'):
          print('parsing msg_id=%s' % msg_id)
          syslog.syslog('parsing msg_id=%s' % msg_id)
        typ, data = imapclient.fetch(msg_id,'(RFC822)')
        message = Parser().parsestr(data[0][1])
        if message:
          abuse = Parser().parsestr(message.get_payload()[2].as_string())
          if is_abuse(message.get_payload()[1]):
            to_email = abuse.get_payload()[0].get('To')
            if to_email and validateEmail(to_email):
              syslog.syslog('unsubscribe user with email %s' % to_email)
              if type(config.get('sql').get('unsubscribe_queries')) == list:
                for query in config.get('sql').get('unsubscribe_queries'):
                  dbcur.execute(query.replace('{EMAIL}',to_email))
              else:
                dbcur.execute(config.get('sql').get('unsubscribe_queries').replace('{EMAIL}',to_email))
          else:
            syslog.syslog('message is not feedback-report format')
    dbcon.commit()

if __name__ == "__main__":
  signal.signal(signal.SIGINT, sigint_handler)
  if "-h" in sys.argv or "--help" in sys.argv:
    print(__doc__)
    sys.exit(0)
  try:
    main()
  except Exception,e:
    print(e)
    sys.exit(1)
