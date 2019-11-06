import os, time, ssl, shutil, hashlib, logging, socket, sys, glob, json, random, base64
from http.client import *


def get_c8y_host():
	return os.environ['C8Y_BASEURL']

def get_c8y_tenant():
	return os.environ['C8Y_TENANT']

def get_c8y_username():
	return os.environ['C8Y_USER']

def get_c8y_password():
	return os.environ['C8Y_PASSWORD']

def get_application_name():
	return os.environ['APPLICATION_NAME']

def platform_request(method, path, body=None, headers=None):

	if not headers: headers = {}

	sslctx = ssl.create_default_context()
	sslctx.check_hostname = False
	sslctx.verify_mode = ssl.CERT_NONE

	host = get_c8y_host()
	useHTTPS = not host.startswith('http://')
	port = 443 if useHTTPS else 80
	if host.endswith('/'): host = host[:-1]
	host = host[ len('https://') if useHTTPS else len('http://') : ]
	if ':' in host:
		port = int(host.split(':')[1])
		host = host.split(':')[0]

	if useHTTPS:
		conn = HTTPSConnection(host=host, port=port, context=sslctx)
	else:
		conn = HTTPConnection(host=host, port=port)

	if 'Authorization' not in headers:
		headers["Authorization"] = "Basic " + base64.b64encode(bytes(f'{get_c8y_tenant()}/{get_c8y_username()}:{get_c8y_password()}', "utf8")).decode()

	headers["Accept"] = "application/json"
	if not "Content-Type" in headers and method != "GET":
		headers["Content-Type"] = "application/json"

	if isinstance(body, dict):
		body = json.dumps(body)

	conn.connect()

	try:
		conn.request(method, path, body=body, headers=headers)
		resp = conn.getresponse()

		respHeaders = {}
		for (k,v) in resp.getheaders():
			respHeaders[k] = v
		respBody = resp.read()
		if resp.getheader("Content-Type") and "json" in resp.getheader("Content-Type") and len(respBody) > 0:
			respBody = json.loads(respBody)
		print(f'{method} to {path} returned status code {resp.status}')

		if not (resp.status >= 200 and resp.status <=299):
			e=Exception("Request to %s failed with %i %s" % (path, resp.status, resp.reason))
			e.respBody = respBody
			e.status = resp.status
			raise e
		return respBody
	finally:
		conn.close()

def get_current_application_id():
	return platform_request('GET', f'/application/applicationsByName/{get_application_name()}')['applications'][0]['id']

def get_application_managed_object_id():
	return platform_request('GET', f'/inventory/managedObjects?type=c8y_Application_{get_current_application_id()}')['managedObjects'][0]['id']

