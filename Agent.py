import json
import socket
import requests
import logging
import urllib2
import time
import netifaces
import os
from IPy import IP
from uptime import uptime
import pyping



'''Updates discovery database of presence of a Fog compute node'''


class Agent:
    def __init__(self):
        # Read server ip
        logging.info("Starting agent")

        with open('config.json') as json_data:
            self.data = json.load(json_data)
            self.server_ip = self.data['server_ip']
            self.poll_time = self.data['poll_time']
            self.anchors = self.data['anchor_nodes']

        #Get node ip. This might not get the right IP address
        self.node_ip = socket.gethostbyname(socket.gethostname())
    #    ip_type = IP(node_ip).iptype()

        self.interface_dict = {}

    '''Repeats tests and reports to discovery server'''
    def agent_daemon(self):
        # After time (defined in config.json) update information in case node has new ip
        while (True):
            # Build request
            #Data should be Net, sys, and stats
            self.update_net()
            self.update_sys()
            self.gather_net_stats()
            self.report_stats()
            time.sleep(self.poll_time)

    def update_net(self):
        # Look through all interfaces and get ip addresses
        for interface in netifaces.interfaces():
            if (not "lo" in interface):
                addr_info = netifaces.ifaddresses(interface)
                for k in addr_info:
                    for i in addr_info[k]:
                        if (not len(i['addr']) == 17):
                            tmp_ip = i['addr']
                            if (len(tmp_ip) == 31):
                                # Cut metadata from IPv6 addr
                                tmp_ip = tmp_ip[:25]
                            self.interface_dict[interface] = tmp_ip

        for interface in self.interface_dict:
            if(IP(self.interface_dict[interface]).iptype() == "PUBLIC"):
                print "Public address found :" + self.interface_dict[interface]
                self.node_ip = self.interface_dict[interface]


    def update_sys(self):
        self.load = os.getloadavg()
        self.up_time = uptime()
        self.sys_stats = {'load':self.load, 'uptime':self.up_time}


    def gather_net_stats(self):
        #Do ping to all anchor nodes
        self.anchor_stats = {}
        for(anchor_ip in self.anchors):
            ping_response = pyping.ping(anchor_ip)
            if(ping_response.ret_code == 0):
                latency = ping_response.avg_rtt
            else:
                latency = -1
            #Do Iperf here
            throughput = 100
            hops = 10
            self.anchor_stats[anchor_ip] = {"latency":latency, "throughput":throughput, "hops": hops}

    def report_stats(self):
        data = {"ip": self.node_ip, "anchor_stats": self.anchor_stats, "system_stats": self.sys_stats}
        req = urllib2.Request('http://' + self.server_ip + ':61112/nodes/register_node')
        req.add_header('Content-Type', 'application/json')
        retry = True
        while (retry):
            try:
                response = urllib2.urlopen(req, json.dumps(data))
            except urllib2.HTTPError as e:
                retry = True
                time.sleep(30)
                logging.warning("Could not make connection to discovery server")
            else:
                retry = False