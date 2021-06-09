import argparse
import os
import subprocess
import re
import sys
import time

def log_message(message, newline=True):
	if newline:
		message += '\n'
		
	sys.stderr.write(message)

# commented out lines help with debugging
# now matches multiline strings
def regmatch(keyStr, inStr):
#	log_message('trying to find "' + keyStr + '" inside "' + inStr + '"')
	m = re.search(keyStr, inStr, re.M)
# 	if m:
# 		log_message("found!")
# 	else:
# 		log_message("nope")

	return m

# supports three styles of matching: 
# space equals space (... = ...\n)
# colon space (...: ...\n)
# json style (...":"...")
def regex_getVal(inStr, keyStr, throwB = True):
	valStr = ''
	
	m = regmatch('.*' + keyStr + ' = (.*)$', inStr)
	if not m: m = regmatch('.*' + keyStr + ': (.*)$', inStr)
	if not m: m = regmatch('.*"' + keyStr + '":"(.*?)"', inStr)
	if not m:
		log_message('[Error] "' + keyStr + '" key not found')
		
		if throwB:
			exit(1)
	else:
		valStr = m.group(1)

	# log_message('>> "' + keyStr + '": "' + valStr + '"')
	return valStr

def pipe(cmdArgs):
	process = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output, error = process.communicate()
	output_str = output.decode('utf-8')
	error_str = error.decode('utf-8')

	# skip over this noisy NON-error. if we get it, then move the real results
	# into the error_str, which is the one we want returned anyway
	if 'AcceptPolicy_block_invoke' in error_str:
		error_str = output_str

# 	log_message("out:" + output_str)
# 	log_message("err: " + error_str)
	return error_str

def upload_package(dict):

	log_message('>> Notarizing: Uploading dmg to Apple')

	error_str = pipe(
		['xcrun', 
			'altool', 
			'--notarize-app', 
			'-t', 'osx', 
			'--primary-bundle-id',	dict['primary_bundle_id'], 
			'-f',					dict['package'],
			'-u',					dict['username'],
			'-p',					dict['password'],
			'--output-format', 		'json'])

	if not 'No errors uploading' in error_str:
		log_message('[Error] Upload failed')
		exit(1)
		
	uuid = regex_getVal(error_str, 'RequestUUID') 
	return uuid

def check_status(dict):
	#log_message('>> Checking status...')
	
	error_str = pipe(
		['xcrun', 
			'altool', 
			'--notarization-info',	dict['uuid'],
			'-u',					dict['username'], 
			'-p',					dict['password'], 
			'--output-format',		'json'])

	statusStr = regex_getVal(error_str, 'Status') 
	
	in_progressB	= statusStr == 'in progress'
	successB		= statusStr == 'success'

	if not in_progressB and not successB:
		log_message(error_str)
		log_message('[Error] Notarization failed')
		exit(1)

	if not in_progressB:
		log_message('\t>> Notarization successful')

	return in_progressB

def staple(dict):
	packageStr = dict['package']

	log_message('>> Stapling')
	error_str = pipe(
		['xcrun', 
			'stapler', 
			'staple', packageStr])

# you can now call this func from another python script, passing in 
# a dict-style argument block instead of actual args.  
# note the key for --primary-bundle-id is actually 'primary_bundle_id'
def call(dict):
	#log_message('dict: ' + str(dict))
	packageStr = dict['package']
	
	if not packageStr.endswith('.dmg'):
		log_message('Supplied package %s is not a dmg file' % packageStr)
		exit(1)

	uuid = upload_package(dict)
	
	# add uuid to "args" dict
	dict['uuid'] = uuid

	# do-while here, instead of while-do, otherwise first check will fail 
	while True:
		log_message('\t>> Notarization in progress. Checking back in 30s')
		time.sleep(30)
		if not check_status(dict):
			break
		
 	staple(dict)

	log_message('[Success] Notarization complete')
	
# if you want to call it from another script, with args, you still can
def main(in_args):
	parser = argparse.ArgumentParser(description="Notarizes supplied dmg by uploading it to apple servers.")
	parser.add_argument("--package", help="Path to the dmg file", action='store', required=True)
	parser.add_argument("--username", help="Apple ID username to use to notarize", action='store', required=True)
	parser.add_argument("--primary-bundle-id", help="Bundle id of package as specified in Info.plist", action='store', required=True)
	parser.add_argument("--password", action='store', help="Password for the appleid.", required=True)
	args = parser.parse_args(in_args)
	call(vars(args))

# and can still call from command line, of course
if __name__ == '__main__':
	main(sys.argv[1:])
