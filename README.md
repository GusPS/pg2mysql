# pg2mysql
Simple scripts for converting a Postgres DB to MySQL db.

This script was created by a specific need for migrating a particular Postgres DB to MySQL and worked ok for this particular scenario.

The other tools that I found online for this kind of tasks were not working the way I needed so wrote this scripts.

There are some things to pay attention and have in mind before using it:

- The main script is the BASH script: Maybe all could be solved inside the Python script, but for me it was faster this way because I only wanted the Python script output SQL sentences without knowing anything about MySQL.
- There is no implementation for passing paramenters: Both script should be opened and modified accordingly to set the DB name, user, server, etc
- The Data Types from Postgres to MySQL may be incomplete. I only converted the types that was present in my DB. If later on other DBs should be migrated, I will add support for mising types. If some type is not covered, it will be outputed as FIXME.
- The logging information and docs inside code could be improved a lot. I just didn't have time to do it. 
- The code asume that the /tmp folder exists, and there will be exported all data as CSV.
- The connection to Postgres is opened as READONLY.
- The export is enconding using UTF-8, and the MySQL db es created with the same enconding. Have a look at the BASH script.
- The MySQL engine is fixed to InnoDB

And the more important thing is to open both scripts and do a simple revision to understand how it work before run them. 

Hope it will be useful. That's the reason for making it public on GitHub.
