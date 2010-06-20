#!/bin/sh

### BEGIN INIT INFO
# Provides:          currentcostd
# Required-Start:    $syslog
# Required-Stop:     $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Starts currentcostd.py at boot.
# Description:       currentcostd.py
### END INIT INFO

set -e

case "$1" in
    start)
        echo "Starting currentcostd"
        /usr/bin/python /usr/local/bin/currentcostd.py --start --setuid=currentcost --setgid=currentcost
        ;;  
    stop)
        echo "Stopping currentcostd"
        /usr/bin/python /usr/local/bin/currentcostd.py --stop
        ;;  
    restart)
                echo "Restartubg currentcostd"
                /usr/bin/python /usr/local/bin/currentcostd.py --restart --setuid=currentcost --setgid=currentcost
        ;;  
    *)  
        echo "Usage: /etc/init.d/currentcostd {start|stop|restart}" >&2 
        exit 1
        ;;  
esac

exit 0
