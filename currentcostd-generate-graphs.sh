#!/bin/sh

rrdtool="/usr/bin/rrdtool"
filename="/var/currentcostd/currentcostd.rrd"
graphpath="/var/currentcostd/static"
title="Power Usage"

$rrdtool graph $graphpath/power-10min.png \
--start end-10m --width 700 --end now --slope-mode \
--vertical-label Watts \
-t "$title (Last 10 minutes)" --alt-autoscale-max \
DEF:Power=$filename:Power:AVERAGE \
DEF:PowerMin=$filename:Power:MIN \
DEF:PowerMax=$filename:Power:MAX \
CDEF:PowerRange=PowerMax,PowerMin,- \
LINE1:PowerMin#0000FF33:"Min" \
LINE1:PowerMax#0000FF33:"Max" \
LINE1:Power#0000FF:"Average" \
"GPRINT:PowerMax:MAX:  Max\: %.0lf" \
"GPRINT:PowerMin:MIN:Min\: %.0lf" \
"GPRINT:Power:AVERAGE:Avg\: %.0lf" \
"GPRINT:Power:LAST:Cur\: %.0lf"

$rrdtool graph $graphpath/power-1day.png \
--start end-1d --width 700 --end now --slope-mode \
--vertical-label Watts \
-t "$title (Last day)" --alt-autoscale-max \
DEF:Power=$filename:Power:AVERAGE \
DEF:PowerMin=$filename:Power:MIN \
DEF:PowerMax=$filename:Power:MAX \
CDEF:PowerRange=PowerMax,PowerMin,- \
LINE1:PowerMin#0000FF33:"Min" \
LINE1:PowerMax#0000FF33:"Max" \
LINE1:Power#0000FF:"Average" \
"GPRINT:PowerMax:MAX:  Max\: %.0lf" \
"GPRINT:PowerMin:MIN:Min\: %.0lf" \
"GPRINT:Power:AVERAGE:Avg\: %.0lf" \
"GPRINT:Power:LAST:Cur\: %.0lf"

$rrdtool graph $graphpath/power-1week.png \
--start end-1w --width 700 --end now --slope-mode \
--vertical-label Watts \
-t "$title (Last Week)" --alt-autoscale-max \
DEF:Power=$filename:Power:AVERAGE \
DEF:PowerMin=$filename:Power:MIN \
DEF:PowerMax=$filename:Power:MAX \
CDEF:PowerRange=PowerMax,PowerMin,- \
LINE1:PowerMin#0000FF33:"Min" \
LINE1:PowerMax#0000FF33:"Max" \
LINE1:Power#0000FF:"Average" \
"GPRINT:PowerMax:MAX:  Max\: %.0lf" \
"GPRINT:PowerMin:MIN:Min\: %.0lf" \
"GPRINT:Power:AVERAGE:Avg\: %.0lf" \
"GPRINT:Power:LAST:Cur\: %.0lf"

$rrdtool graph $graphpath/power-1month.png \
--start end-1m --width 700 --end now --slope-mode \
--vertical-label Watts \
-t "$title (Last Month)" --alt-autoscale-max \
DEF:Power=$filename:Power:AVERAGE \
DEF:PowerMin=$filename:Power:MIN \
DEF:PowerMax=$filename:Power:MAX \
CDEF:PowerRange=PowerMax,PowerMin,- \
LINE1:PowerMin#0000FF33:"Min" \
LINE1:PowerMax#0000FF33:"Max" \
LINE1:Power#0000FF:"Average" \
"GPRINT:PowerMax:MAX:  Max\: %.0lf" \
"GPRINT:PowerMin:MIN:Min\: %.0lf" \
"GPRINT:Power:AVERAGE:Avg\: %.0lf" \
"GPRINT:Power:LAST:Cur\: %.0lf"


$rrdtool graph $graphpath/power-1year.png \
--start end-1y --width 700 --end now --slope-mode \
--vertical-label Watts \
-t "$title (Last Year)" --alt-autoscale-max \
DEF:Power=$filename:Power:AVERAGE \
DEF:PowerMin=$filename:Power:MIN \
DEF:PowerMax=$filename:Power:MAX \
CDEF:PowerRange=PowerMax,PowerMin,- \
LINE1:PowerMin#0000FF33:"Min" \
LINE1:PowerMax#0000FF33:"Max" \
LINE1:Power#0000FF:"Average" \
"GPRINT:PowerMax:MAX:  Max\: %.0lf" \
"GPRINT:PowerMin:MIN:Min\: %.0lf" \
"GPRINT:Power:AVERAGE:Avg\: %.0lf" \
"GPRINT:Power:LAST:Cur\: %.0lf"

