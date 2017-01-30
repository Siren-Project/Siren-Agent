import json
import socket
import requests
import logging
import urllib2
import time
'''Updates discovery database of presence of a Fog compute node'''
class Agent:

    #Read server ip
    logging.info("Starting agent")

    with open('config.json') as json_data:
        data = json.load(json_data)
        server_ip = data['server_ip']
        poll_time = data['poll_time']

    #Get node ip
    node_ip = socket.gethostbyname(socket.gethostname())

    #Build request
    data = {"ip":node_ip}
    req = urllib2.Request('http://'+server_ip+':61112/nodes/register_node')
    req.add_header('Content-Type', 'application/json')

    retry=True

    #Send request. Check response to see if was successful
    while(retry):
        try:
            response = urllib2.urlopen(req, json.dumps(data))
        except urllib2.HTTPError as e:
                retry = True
                time.sleep(30)
                logging.warning("Could not make connection to discovery server")
        else:
            retry = False

    #After time (defined in config.json) update information in case node has new ip
    while(True):
        time.sleep(poll_time)
        # Get node ip
        node_ip = socket.gethostbyname(socket.gethostname())

        # Build request
        data = {"ip": node_ip}
        req = urllib2.Request('http://' + server_ip + ':61112/nodes/register_node')
        req.add_header('Content-Type', 'application/json')
        try:
            response = urllib2.urlopen(req, json.dumps(data))
        except urllib2.HTTPError as e:
            pass
