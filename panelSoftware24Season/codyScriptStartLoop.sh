#! /bin/bash

while :

do
        if pgrep -x "CODALEMA_DAQ" > /dev/null
        then
                :
                #echo  'running'
        else
                echo 'cody not running... attempting to start script'
                /home/retcr/deployment/CODALEMA_DAQ

        fi


        sleep 10

done