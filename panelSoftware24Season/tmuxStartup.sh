#!/bin/bash
#sleep 1
source /home/retcr/.bash_profile
if tmux has-session  > /dev/null 2>&1; then
    :
else
        tmux new-session -d -s stationTmux

        tmux send-keys 'python3 /home/retcr/deployment/panelSoftware24Season/twoPanels.py' 'C-m'
        tmux rename-window 'Panels'
        tmux select-window -t stationTmux:0
        tmux split-window -h
        tmux send-keys '/home/retcr/codyScriptStartLoop.sh' 'C-m'

        #tmux send-keys 'sleep 15' 'C-m'
        #tmux send-keys '/home/retcr/deployment/CODALEMA_DAQ' 'C-m'
        tmux select-pane -t stationTmux:0.1
        tmux split-window -v
        tmux resize-pane -y 2
        tmux send-keys 'uptime' 'C-m'
        tmux -2 attach-session -t stationTmux

fi