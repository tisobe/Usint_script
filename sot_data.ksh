#!/bin/ksh

#
# run the query in sot_data.sql and save the output in /proj/web-icxc/cgi-bin/obs_ss/sot_data.sql
#

SYBASE=/soft/sybase
export SYBASE
passwd=`cat /data/mta4/MTA/data/.ocatpasswd`
/usr/local/bin/sqsh -h -Ubrowser -Socatsqlsrv -P$passwd -s ^ -i /proj/web-icxc/cgi-bin/obs_ss/sot_data.sql -w2100

