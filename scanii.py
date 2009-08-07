#!/usr/bin/env python
# encoding: utf-8
"""
scanii.py

Created by Rafael Ferreira on 2009-07-19.
Copyright (c) 2009 Uva Software, LLC. For Licensing see LICENSE.

Note:
	* crendetials can be passed or stored in a environment varialbe called SCANII_CRED
"""

import sys, os.path, logging, optparse 
import urllib2
import time

try:
	import json
except:
	import simplesjon as json
	

log = logging.getLogger('scanii')

__version__ = "0.2"
__license__ ="MIT/X11"

DESC = "Scanii's python command line client"
API_URL = "http://scanii.com/a/s/1/"
ENV_VAR = 'SCANII_CRED'

class Client(object):
	"""
	Simple and reusable client for scanii.com
	"""
	def __init__(self,url, key, secret):
		self.url = url
		self.key = key
		self.secret = secret
		self.infected = []
		self.clean= []
		
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

		passman.add_password(None, self.url, self.key, self.secret)

		authhandler = urllib2.HTTPBasicAuthHandler(passman)
		# create the AuthHandler

		opener = urllib2.build_opener(authhandler)

		urllib2.install_opener(opener)
		
		log.debug('client init with endpoint %s' % url)			
		
	def api_call(self,data):
	
		req = urllib2.Request(self.url, data )
		resp = urllib2.urlopen(req)
		j = json.loads(resp.read())
		
		log.debug('raw json response: %s' % j)
		
		return j

	def scan(self, filename):
		""" converts a file into bytes and scans it using the internal api"""
		
		file = open(filename, 'r')
		try:
			return self.api_call(file.read() )
			
	
		finally:
			file.close()
			
		
def main():
	if len(sys.argv) < 2:
		sys.argv.append('-h')
	
	parser = optparse.OptionParser(usage="scanii.py [options] PATH",description=DESC,version=__version__)

	parser.add_option("-c","--cred", dest="cred", help="your API key and secret in KEY:SECRET format", action="store")
	parser.add_option("-v","--verbose", dest="verbose", help="runs in verbose mode", action="store_true", default=False)
	parser.add_option("-r","--recursive", dest="recursive", help="descends throught PATH pulling all files", action="store_true", default=False)
	parser.add_option("-u","--url", dest="url", help="API address to be used instead of scanii's default", action="store", default=API_URL)
	#parser.add_option("-a","--address", dest="address", help="the name/ip to listen on (if server) or to send to (if client)", action="store")
	
	# client only options
	#client_options = optparse.OptionGroup(parser,"Client options")
	#client_options.add_option("-k","--packet-size", action="store", dest="packet_size", help="packet size in kbytes")
	#client_options.add_option("-n","--packet-count", action="store", dest="packet_count", help="number of packets to send before quitting")
	#parser.add_option_group(client_options)
	

	(options,args) = parser.parse_args()

	# add ch to logger

	if (options.verbose):
		ch = logging.StreamHandler()
		# create formatter
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
		ch.setFormatter(formatter)
		log.setLevel(logging.DEBUG)		
		log.addHandler(ch)
	
	target = sys.argv[-1]
	log.info('run target %s' % sys.argv[-1])
	log.info('discovering credentials, first from args')
	key = None
	secret = None
	
	try: 
		key,secret = options.cred.split(':')
	except: 
		pass
		
	if key is None or secret is None:
		log.info('trying to pull creds from environment')
		try:
			key, secret = os.environ[ENV_VAR].split(':')
		except:
			print('could not load your api credentials, try using -c')
			sys.exit(1)
	
	
	log.debug('using key %s secret %s' %(key,secret))
	
	files  = []
		
	print("Scanii python client version %s" % __version__)
	print("Using url: %s" % options.url)
	print("Using API key: %s" % key)
	client = Client(options.url, key, secret)
	
	print('')
	print('Building file listing for target %s'  % target )
	
	if os.path.isfile(target):
		files.append(target)
		
	elif os.path.isdir(target):
		if options.recursive is True:
			for root, dir, names in os.walk(target):
				for name in names:
					files.append(os.path.join(root,name) )
		else:
			for file in os.listdir(target):
				if os.path.isfile(os.path.join(target,file)):
					files.append(os.path.join(target,file) )	
	
	print('Scaniing %s file(s)' % len(files))
	total_infected = 0
	total_clean = 0
	total_error = 0
	
	for file in files:
		
		start = time.time()
		
		try:
			j = client.scan(file)
		
		except Exception, ex:
			print('fatal error [%s] while scanning file %s' % (ex,file) )
			continue
		
		
		elapsed = time.time() - start
		
		result = 'error'

		if j['status'] == 'infected':
			result = 'INFECTED with virus %s ' % j['virus'][0]
			total_infected +=1

		elif j['status'] == 'clean':
			result = 'CLEAN' 
			total_clean +=1

		elif j['status'] == 'oops':
			result = 'ERROR - %s' % j['reason']
			total_error +=1
						
		print '%s: %s  in %.2f msec' % (file, result, elapsed*1000)
		
	print('')
	print('-------- Scan Summary --------')
	print('   infected files: %s' % total_infected)
	print('   clean files: %s' % total_clean)		
	print('   errors: %s' % total_error )
		

if __name__ == '__main__':
	main()

