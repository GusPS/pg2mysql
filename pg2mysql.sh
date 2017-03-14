#!/bin/bash
#This is the main script that must be called.
#The goal is to create an export of scheme and data, which will be saved on a temp folder as CSV. Then it will be imported by LOAD INFILE command.

#Set MySQL Db name to create. This will be droped firts if exists.
MYSQL_DBNAME=mydatabase

#Call the Python conversion script and store it in temp folder
./pg2mysql.py > /tmp/ddl_export.mysql

mysql -e "drop database if exists ${MYSQL_DBNAME}"
mysql -e "create database ${MYSQL_DBNAME} CHARACTER SET utf8 COLLATE utf8_general_ci;"
mysql --local-infile -v ${MYSQL_DBNAME} < /tmp/ddl_export.mysql

#Remove temporary files created
rm /tmp/ddl_export.mysql
rm /tmp/pg2mysql_tabledata_*.csv
