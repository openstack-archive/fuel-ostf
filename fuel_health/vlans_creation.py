from subprocess import Popen, PIPE
import requests
import os

# from fuel_health import config
#
# conf = config.FuelConfig()


#os.chdir('/etc/sysconfig/network-scripts/')
uri = 'http://172.18.164.133:8000/api/'
clusters_ids = []
network_setting_json = [{}]
created_vlans_id = []


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
                    created_vlans_id.append(str(vlan_id))
                    cidr = netw['cidr']

                    test_res = cidr.split('.')
                    if test_res[-1].split('/')[-1] == '24':
                        ip_addr = '%s.%s.%s.253/24' % (test_res[0], test_res[1], test_res[2])
                        net_mask = netw['netmask']
                        cmd_add_vlan = 'vconfig add eth0 ' + str(vlan_id)
                        cmd_ip_add = 'ip a add' + ip_addr + 'dev eth0.%s' % (str(vlan_id))
                        cmd_link_ip_to_dev = 'ip link set up dev eth0.%s' % (str(vlan_id))
                        try:
                            p = Popen(cmd_add_vlan, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not create vlan %s' % (str(vlan_id))

                        try:
                            p = Popen(cmd_ip_add, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_ip_add

                        try:
                            p = Popen(cmd_link_ip_to_dev, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_link_ip_to_dev


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

                        cmd_add_vlan = 'vconfig add eth0 ' + str(vlan_id)
                        cmd_ip_add = 'ip a add' + ip_addr + 'dev eth0.%s' % (str(vlan_id))
                        cmd_link_ip_to_dev = 'ip link set up dev eth0.%s' % (str(vlan_id))
                        try:
                            p = Popen(cmd_add_vlan, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not create vlan %s' % (str(vlan_id))

                        try:
                            p = Popen(cmd_ip_add, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_ip_add

                        try:
                            p = Popen(cmd_link_ip_to_dev, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_link_ip_to_dev


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

                        cmd_add_vlan = 'vconfig add eth0 ' + str(vlan_id)
                        cmd_ip_add = 'ip a add' + ip_addr + 'dev eth0.%s' % (str(vlan_id))
                        cmd_link_ip_to_dev = 'ip link set up dev eth0.%s' % (str(vlan_id))
                        try:
                            p = Popen(cmd_add_vlan, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not create vlan %s' % (str(vlan_id))

                        try:
                            p = Popen(cmd_ip_add, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_ip_add

                        try:
                            p = Popen(cmd_link_ip_to_dev, shell=True, stdout=PIPE, stderr=PIPE)
                            out, err = p.communicate()
                            print out, err
                        except Exception:
                            print 'Can not execute command %s' % cmd_link_ip_to_dev



def remove_created_vlans():
    for vlan_id in created_vlans_id:
        cmd = 'vconfig rem eth0.%s' % (str(vlan_id))
        try:
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            print out, err
        except Exception:
            print 'Can not execute command %s' % cmd

get_cluster_data()
#create_management_vlans()
print clusters_ids
print network_setting_json
create_management_vlans()
create_vm_vlans()
create_storage_vlans()
