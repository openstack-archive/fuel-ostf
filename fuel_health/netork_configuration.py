from subprocess import Popen, PIPE
import requests
import os

# from fuel_health import config
#
# conf = config.FuelConfig()


os.chdir('/etc/sysconfig/network-scripts/')
uri = 'http://172.18.164.133:8000/api/'
clusters_ids = []
network_setting_json = [{}]


def get_clusters():
    url = uri + 'clusters/'
    cluster_json = requests.get(url).json()
    for cluster in cluster_json:
        clusters_ids.append(cluster['id'])
    return clusters_ids


def get_cluster_data():
    get_clusters()
    for id in clusters_ids:
        url = uri + 'clusters/' + str(id) + '/network_configuration/'
        network_setting_json.append(requests.get(url).json())

        return network_setting_json


def create_management_vlans():
    for el in network_setting_json:
        if el:
            for netw in el['networks']:
                if netw['name'] == 'management':
                    vlan_id = netw['vlan_start']

                    cidr = netw['cidr']

                    test_res = cidr.split('.')
                    if test_res[-1].split('/')[-1] == '24':
                        ip_addr = '%s.%s.%s.253' %(test_res[0], test_res[1], test_res[2])
                        net_mask = netw['netmask']

                        file = open("ifcfg-eth0." + str(vlan_id), "w")
                        file.write('DEVICE=eth0.%s\nIPADDR=%s\nNETMASK=%s\nBOOTPROTO=none\nONBOOT=yes\nUSERCTL=no\nVLAN=yes\n' % (str(vlan_id), ip_addr, net_mask))
                        file.close()


def create_vm_vlans():
    for el in network_setting_json:
        if el:
            for netw in el['networks']:
                if netw['name'] == 'fixed':
                    vlan_id = netw['vlan_start']

                    cidr = netw['cidr']

                    test_res = cidr.split('.')
                    if test_res[-1].split('/')[-1] == '24':
                        ip_addr = '%s.%s.%s.253' %(test_res[0], test_res[1], test_res[2])
                        net_mask = netw['netmask']

                        file = open("ifcfg-eth0." + str(vlan_id), "w")
                        file.write('DEVICE=eth0.%s\nIPADDR=%s\nNETMASK=%s\nBOOTPROTO=none\nONBOOT=yes\nUSERCTL=no\nVLAN=yes\n' % (str(vlan_id), ip_addr, net_mask))
                        file.close()


def create_storage_vlans():
    for el in network_setting_json:
        if el:
            for netw in el['networks']:
                if netw['name'] == 'storage':
                    vlan_id = netw['vlan_start']

                    cidr = netw['cidr']

                    test_res = cidr.split('.')
                    if test_res[-1].split('/')[-1] == '24':
                        ip_addr = '%s.%s.%s.253' %(test_res[0], test_res[1], test_res[2])
                        net_mask = netw['netmask']

                        file = open("ifcfg-eth0." + str(vlan_id), "w")
                        file.write('DEVICE=eth0.%s\nIPADDR=%s\nNETMASK=%s\nBOOTPROTO=none\nONBOOT=yes\nUSERCTL=no\nVLAN=yes\n' % (str(vlan_id), ip_addr, net_mask))
                        file.close()





def restart_network():
    command = 'service network restart'
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()


def verify_created_networks():
    command = 'cat /proc/net/vlan/config'
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    print out, err


get_cluster_data()
#create_management_vlans()
print clusters_ids
print network_setting_json
create_management_vlans()
create_vm_vlans()
create_storage_vlans()
restart_network()
verify_created_networks()
