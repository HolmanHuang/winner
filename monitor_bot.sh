#! /bin/bash 
# Monitor for the processor if die then restart

while true
do
 if ps -ef | grep SmmbCase1.py | grep -v grep > /dev/null ; then
     date >> monitor.log
     echo "up" >> monitor.log
 else
     echo "down" >> monitor.log
     date >> monitor.log
     ./start_bot.sh
 fi    
 sleep 10
done 
