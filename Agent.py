import json
import socket
import requests
import logging
import urllib2
import time
import netifaces
import os
from IPy import IP
import iperf3
from uptime import uptime
import pyping



'''Updates discovery database of presence of a Fog compute node'''


class Agent:
    def __init__(self):
        # Read server ip
        print "Starting agent"

        with open('config.json') as json_data:
            self.data = json.load(json_data)
            self.server_ip = self.data['server_ip']
            self.poll_time = self.data['poll_time']
            self.anchors = self.data['anchor_nodes']

        # Get node ip. This might not get the right IP address but will be changed if public ip is given
        # Do not use gethostname as container will have different hostname
        self.node_ip = None#socket.gethostbyname(socket.gethostname())
        #    ip_type = IP(node_ip).iptype()

        self.interface_dict = {}

        self.agent_daemon()

    '''Repeats tests and reports to discovery server'''
    def agent_daemon(self):
        # After time (defined in config.json) update information in case node has new ip
        print "Daemon started"
        while (True):
            # Build request
            #Data should be Net, sys, and stats
            self.update_net()
            self.update_sys()
            self.gather_net_stats()
            self.report_stats()
            print "Stats reported. Waiting " + str(self.poll_time) + " seconds"
            time.sleep(self.poll_time)

    '''Get network information from system'''
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
                                tmp_ip = tmp_ip.split('%')
                            try:
                                IP(tmp_ip)
                                self.interface_dict[interface] = tmp_ip
                            except:
                                logging.warning("Ignoring invalid IP %s", tmp_ip)

        for interface in self.interface_dict:
            if(IP(self.interface_dict[interface]).iptype() == "PUBLIC"):
                print "Public address found :" + self.interface_dict[interface]
                self.node_ip = self.interface_dict[interface]
        if self.node_ip == None and len(self.interface_dict)>0:
            self.node_ip = self.interface_dict.values()[0]


    '''Get information about the system'''
    def update_sys(self):
        self.load = os.getloadavg()
        self.up_time = uptime()
        self.sys_stats = {'load':self.load, 'uptime':self.up_time}
        return self.sys_stats

    '''Perform network tests against anchor nodes'''
    def gather_net_stats(self):
        #Do ping to all anchor nodes
        self.anchor_stats = {}
        for anchor_ip in self.anchors:
            try:
                ping_response = pyping.ping(anchor_ip)
                if(ping_response.ret_code == 0):
                    latency = ping_response.avg_rtt
                else:
                    latency = -1
            except:
                latency = -1
                logging.warning("Not root. Cannot perform ping.")


            #Do Iperf here.
            throughput = -1

            #Check to see if not osx (does not work with osx)
            if(not "Darwin" in os.uname()):
                client = iperf3.Client()
                client.duration = 10
                client.server_hostname = anchor_ip
                client.port = 5001
                result = client.run()
                throughput = result.sent_Mbps
            else:
                logging.warning("OSX not supported")

            #Do tracert here
            hops = 10


            self.anchor_stats[anchor_ip] = {"latency":latency, "throughput":throughput, "hops": hops}
            return self.anchor_stats

    '''Send all stats to discovery server'''
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


if __name__ == '__main__':
    Agent()