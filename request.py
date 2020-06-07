from requests import Request, Session
import re

session = Session()
url, params, body, header = [], [], [], []

## Load the OAuth site and get CSRF token
url.append("https://gymkhana.iitb.ac.in/profiles/oauth/authorize/")
params.append({
	'client_id': '18fofSMufkpujkg4WAPHgsJrRAsTfEF1TvpN4etw',
	'scope': 'basic profile insti_address program',
	'redirect_uri': 'http://yearbook.sarc-iitb.org/',
	'response_type': 'token'
})
body.append(None)
header.append(None)
req = session.get(url[-1], params=params[-1], data=body[-1], headers=header[-1])

## Send the POST request to SSO site, using SSO
csrfmiddlewaretoken = [y for y in req.text.split('\n') if re.search("csrfmiddle", y)]
csrfmiddlewaretoken = csrfmiddlewaretoken[0].split('"')[-2]

url.append(req.url)
# params.append(params[0])
params.append(None)
body.append({
	'csrfmiddlewaretoken': csrfmiddlewaretoken,
	'next': '',
	'httpd_username': '',
	'httpd_password': ''
})
header.append({
	'Origin': 'https://gymkhana.iitb.ac.in',
	'Referer': req.url
})
post = session.post(url[-1], params=params[-1], data=body[-1], headers=header[-1], allow_redirects=False)

redirect = None

## Check if authorisation page is skipped
if re.search('access_token', post.headers['Location']):
	## Skipped. Print the access token
	# print('Skipping to Yearbook')
	
	redirect = re.sub('http', 'https', post.headers['Location'])
else:
	## Authorisation page is to be filled. Continue with redirect
	# print('Continuing with authorisation')
	
	post = session.post(post.url)
	url.append(req.url)
	# params.append(params[0])
	params.append(None)
	body.append({
		'csrfmiddlewaretoken': csrfmiddlewaretoken,
		'redirect_uri': 'http://yearbook.sarc-iitb.org/',
		'scope': 'basic program insti_address profile',
		'client_id': '18fofSMufkpujkg4WAPHgsJrRAsTfEF1TvpN4etw',
		'state': '',
		'response_type': 'token',
		'code_challenge': '',
		'code_challenge_method': '',
		'scopes_array': ['program', 'insti_address', 'profile'],
		'allow': 'Authorize'
	})
	header.append(header[1])
	auth = session.post(url[-1], params=params[-1], data=body[-1], headers=header[-1], allow_redirects=False)
	## Location
	redirect = re.sub('http', 'https', auth.headers['Location'])

## Work with a new session
sess_new = Session()
redirect = re.sub('#', '?', redirect)
## Try and paste the following output in your browser
# print(redirect)
## Escape '&' for bash
redirect = re.sub('&', '\\&', redirect)
# print(redirect)

import os
command = [
	'wget',
	'--keep-session-cookies',
	'--save-cookies cookie.tmp',
	'--output-document=/dev/null',
	redirect
]
# print(" ".join(command))
os.system(" ".join(command))
