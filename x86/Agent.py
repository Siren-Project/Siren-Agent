'''Updates discovery database of its presence'''
import json
import socket
import requests
import urllib2
import time

class Agent:

    #Read server ip
    print "Starting agent"

    with open('config.json') as json_data:
        data = json.load(json_data)
        server_ip = data['server_ip']

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
        else:
            retry = False

    #After long time (10hrs) update information in case node has new ip
    while(True):
        time.sleep(60000)
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
