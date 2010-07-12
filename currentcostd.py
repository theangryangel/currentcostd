#!/usr/bin/env python

import os, stat, atexit, time, sys, serial, rrdtool, optparse, pwd, grp, Queue, BaseHTTPServer, threading, datetime
from xml.dom import minidom
from signal import SIGTERM 

class ccDaemon:
	def __init__(self, pidfile, conf, rrd, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		if (conf.foreground != True):
			self.stdin = stdin
			self.stdout = stdout
			self.stderr = stderr

		self.pidfile = pidfile
		self.conf = conf
		self.rrd = rrd
		self.uid = 0
		self.gid = 0

		# Translate user and group name to uid and gid
		if self.conf.user != None:
			self.uid = pwd.getpwnam(self.conf.user)[2]
		if self.conf.group != None:
			self.gid = grp.getgrnam(self.conf.group)[2]
	
	def daemonize(self):
		"""
		do the UNIX double-fork magic, see Stevens' "Advanced 
		Programming in the UNIX Environment" for details (ISBN 0201563177)
		http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
		"""
		try: 
			pid = os.fork() 
			if pid > 0:
				# exit first parent
				sys.exit(0) 
		except OSError, e: 
			sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)
	
		# decouple from parent environment
		os.chdir("/") 
		os.setsid() 
		os.umask(0) 
	
		# do second fork
		try: 
			pid = os.fork() 
			if pid > 0:
				# exit from second parent
				sys.exit(0) 
		except OSError, e: 
			sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1) 
	
		# redirect standard file descriptors
		sys.stdout.flush()
		sys.stderr.flush()
		si = file(self.stdin, 'r')
		so = file(self.stdout, 'a+')
		se = file(self.stderr, 'a+', 0)
		os.dup2(si.fileno(), sys.stdin.fileno())
		os.dup2(so.fileno(), sys.stdout.fileno())
		os.dup2(se.fileno(), sys.stderr.fileno())

		try:
			# Switch uid and gid
			if (self.gid > 0):
				os.setgid(self.gid)
			if (self.uid > 0):
				os.setuid(self.uid)
		except e:
			sys.stderr.write("Failed to switch UID or GID: %d (%s)\n" % (e.errno, e.strerror))

		# write pidfile
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)
	
	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		"""
		Start the daemon
		"""
		# Check for a pidfile to see if the daemon already runs
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if pid:
			message = "pidfile %s already exist. Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)
		
		# Start the daemon
		if (self.conf.foreground != True):
			self.daemonize()
		self.run()

	def stop(self):
		"""
		Stop the daemon
		"""
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
	
		if not pid:
			message = "pidfile %s does not exist. Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process	
		try:
			while 1:
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print str(err)
				sys.exit(1)

	def restart(self):
		"""
		Restart the daemon
		"""
		self.stop()
		self.start()

	def run(self):
		print "Starting main loop."
		try:
			ser = serial.Serial(port=self.conf.serialport, baudrate=57600, parity=serial.PARITY_NONE, 
					stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=None
				)
			ser.open()
			ser.isOpen()

			if (self.conf.wwwport > 0):
				www = ccWWW(self.conf.wwwport)

			while True:
				line = ser.readline()
				if len(line)>0:
					line = line.strip()
					if line.startswith('<msg>') and line.endswith('</msg>') and line.find('<hist>')==-1:
						xmldoc = minidom.parseString(line)
						time_nodes = xmldoc.getElementsByTagName('time')
						temperature_nodes = xmldoc.getElementsByTagName('tmpr')
						watts_nodes = xmldoc.getElementsByTagName('ch1')[0].getElementsByTagName('watts')
						time_str = time_nodes[0].childNodes[0].nodeValue
						temperature_str = temperature_nodes[0].childNodes[0].nodeValue
						watts_str = watts_nodes[0].childNodes[0].nodeValue
						power = int(watts_str)
						temperature = float(temperature_str)
						last['power'] = power
						last['temperature'] = temperature
						last['time'] = str(datetime.datetime.now())
						self.rrd.update(power, temperature)

		except KeyboardInterrupt:
			print "Dying."
			if (self.conf.wwwport > 0):
				www.exit()

class rrdFront():
	def __init__(self, path):
		self.rrd = path

	def exists(self):
		return os.path.exists(self.rrd)
	
	def create(self):
		print "Creating RRD"
		rrdtool.create(
			self.rrd,
			'--step', '6', 
			'DS:Power:GAUGE:180:0:U', 'DS:Temperature:GAUGE:180:U:U',
			'RRA:AVERAGE:0.5:1:3200',
			'RRA:AVERAGE:0.5:6:3200',
			'RRA:AVERAGE:0.5:36:3200',
			'RRA:AVERAGE:0.5:144:3200',
			'RRA:AVERAGE:0.5:1008:3200',
			'RRA:AVERAGE:0.5:4320:3200',
			'RRA:AVERAGE:0.5:52560:3200',
			'RRA:AVERAGE:0.5:525600:3200',
			'RRA:MIN:0.5:1:3200',
			'RRA:MIN:0.5:6:3200',
			'RRA:MIN:0.5:36:3200',
			'RRA:MIN:0.5:144:3200',
			'RRA:MIN:0.5:1008:3200',
			'RRA:MIN:0.5:4320:3200',
			'RRA:MIN:0.5:52560:3200',
			'RRA:MIN:0.5:525600:3200',
			'RRA:MAX:0.5:1:3200',
			'RRA:MAX:0.5:6:3200',
			'RRA:MAX:0.5:36:3200',
			'RRA:MAX:0.5:144:3200',
			'RRA:MAX:0.5:1008:3200',
			'RRA:MAX:0.5:4320:3200',
			'RRA:MAX:0.5:52560:3200',
			'RRA:MAX:0.5:525600:3200'
		)

	def update(self, power, temperature):
		print "Updating."
		rrdtool.update(self.rrd, "N:%d:%.1f" % (power, temperature) )

	def graph10min(self, path='/tmp/currentcostd-10min.png'):
		rrdtool.graph(
			path,
			'--start', 'end-10m',
			'--width', '700',
			'--end', 'now',
			'--slope-mode',
			'--no-legend',
			'--vertical-label', 'Watts',
			'--lower-limit', '0', 
			'--alt-autoscale-max',
			'DEF:Power=%s:Power:AVERAGE' % self.rrd, 
			'LINE4:Power#0000FF:"Average"'
		)

class ccWWWHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			if self.path.startswith('/static/'):
				self.__serve_static()
			else:
				self.__serve_index()
		except Exception, e:
			self.__serve_error()

	def __serve_index(self):
		if self.path != "/":
			self.send_error(404, "File not found")
			return
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write( '<html><style type="text/css">@import url(/static/style.css);</style><title>CurrentCost</title><body><div id="power"><span class="title">Power:</span>%s</div><div id="temperature"><span class="title">Temp:</span>%s</div><div id="datetime"><span class="title">Last Updated:</span>%s</div></body></html>' % (last['power'], last['temperature'], last['time']) )

	def __serve_static(self):
		"""
		Serve static files.
		"""
		path = "%s%s" % (wwwroot, self.path.replace("/static/", "", 1))

		if os.path.isfile(path):
			base, ext = os.path.splitext(path)
			if ext == '.css':
				type = 'text/css'
				mode = 'r'
			elif ext == '.js':
				type = 'text/javascript'
				mode = 'r'
			else:
				type = 'application/octet-stream'
				mode = 'rb'
		
			fd = open(path, mode)
			file_info = os.stat(path)
		
			self.send_response(200)
			self.send_header("Content-type", type)
			self.send_header("Content-Length", str(file_info[stat.ST_SIZE]))
			self.end_headers()
		
			# Output file data
			self.wfile.write(fd.read())
		
			fd.close()
		else:
			self.send_error(404, "File not found")

	def __serve_error(self):
		import traceback
		self.send_error(500, "<pre>%s</pre>" % (traceback.format_exc()))

class ccWWW(threading.Thread):
	def __init__(self, port=8080):
		threading.Thread.__init__(self)
		self.httpd = BaseHTTPServer.HTTPServer(("", port), ccWWWHandler)
		self.start()

	def run(self):
		self.httpd.serve_forever()

	def exit(self):
		self.httpd.shutdown()

if __name__ == "__main__":
	parser = optparse.OptionParser(version="%prog 0.1")
	parser.add_option("--start", action="store_true", dest="start", help="Starts the daemon")
	parser.add_option("--stop", action="store_true", dest="stop",
		help="Stops the daemon")
	parser.add_option("--restart", action="store_true", dest="restart",
		help="Restarts the daemon")
	parser.add_option("--createrrd", action="store_true", dest="createrrd",
		help="Creates the rrd.")
	parser.add_option("--pid", dest="pid",
		default="/tmp/currentcostd.pid",
		help="path to PID file.")
	parser.add_option("--foreground", action="store_true", dest="foreground",
		help="Prevents a fork (for debugging purposes - also prevents stdin, stdout, stderr from being redirected.).")
	parser.add_option("--wwwport", dest="wwwport",
		default=8080,
		help="Port to run WWW server on. Defaults to 8080. Setting to 0 disables.")
	parser.add_option("--wwwroot", dest="wwwroot",
		default="/var/currentcostd/static/",
		help="Base path for static files served by www server.")
	parser.add_option("--serialport", dest="serialport",
		default='/dev/ttyUSB0',
		help="Port to listen for CurrentCost data on. Defaults to /dev/ttyUS0.")
	parser.add_option("--setuid", dest="user",
		help="Sets the user for the daemon to run as (currently unused).")
	parser.add_option("--setgid", dest="group",
		help="Sets the group for the daemon to run as (currently unused).")
	parser.add_option("--setrrd", dest="rrd",
		default="/var/currentcostd/currentcostd.rrd",
		help="Sets the path to the rrd file.")

	if len(sys.argv) < 2:
		parser.print_usage()
		sys.exit(2)

	(options, args) = parser.parse_args()

	"""
	Is this the right way to implement this? Given that we only read in the WWW thread I have
	absolutely no idea when it comes to python... My brain thinks this is dirty tho..
	"""
	last = {'power': 0, 'temperature': 0, 'time': 'Unknown'}
	wwwroot = options.wwwroot
	rrd = rrdFront(options.rrd)
	daemon = ccDaemon(options.pid, options, rrd)
	if options.createrrd == True:
		rrd.create()
	if options.start == True:
		daemon.start()
	elif options.stop == True:
		daemon.stop()
	elif options.restart == True:
		daemon.restart()
	else:
		print "Missing start, stop or restart command."
		sys.exit(2)

	sys.exit(0)

