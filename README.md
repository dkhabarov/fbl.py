fbl.py - Simple script to handle ISP's [feedback loops](http://en.wikipedia.org/wiki/Feedback_loop_%28email%29) emails 
(when they forward you all emails on which users clicked 'Report as Spam').
Working as a IMAP Client with SSL/TLS.
Also possible run query to mysql database, for example auto unsubscribe users.

Copyright © 2015 Denis Khabarov aka 'Saymon21'
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

```
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
```

Example usage:

```
pip install -r requirements.txt
./fbl.py /path/to/fbl.conf.yml
```

Add to crontab:
```
0 */1 * * * /path/to/fbl.py /path/to/fbl.conf.yml
```
