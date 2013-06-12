import yaml

from etc.classes import controller_classes, compute_classes, quantum_classes
from etc.ubuntu_resources import resources


class SanityConf(object):
    def __init__(self,
                 username='root',
                 password='r00tme',
                 ssh_key=None,#'etc/id_rsa',
                 nodes_yaml='etc/nodes.yaml'):

        self.username = username
        self.password = password
        self.ssh_key = ssh_key

        nodes_yaml = yaml.load(open(nodes_yaml, 'r').read())
        self.environment = {}
        for i in nodes_yaml['environment']['nodes']:
            role = nodes_yaml['environment']['nodes'][i]['role']
            ip_addr = nodes_yaml['environment']['nodes'][i]['interfaces']['eth0']['ip-address']
            if self.environment.get(role, None) is None:
                self.environment[role] = []
            self.environment[role].append(ip_addr)

        self.cont_res = self.get_res_by_type(resources, controller_classes)
        self.comp_res = self.get_res_by_type(resources, compute_classes)
        self.quantum_res = self.get_res_by_type(resources, quantum_classes)

    def get_res_by_type(self, resources, classes):
        res = {'service': set(),
               'package': set(),
               'file': set()}
        for i in classes:
            temp = resources.get(i, None)
            if temp is not None:
                for i in temp.keys():
                    res[i].update(set(temp[i]))
        return res


if __name__ == "__main__":
  s = SanityConf()
  print "env: %s" % s.environment
  print "cont_res: %s" % s.cont_res
  print "comp_res: %s" % s.comp_res
