from plumbum import SshMachine
from rpyc.utils.zerodeploy import DeployedServer
from rpyc.core.service import ModuleNamespace, Slave

import yaml
import os
import os.path as P
import sys

class LocalMachine:
    def classic_connect(self):
        return LocalEnv()
    
    def close(self):
        pass

class LocalEnv:
    def __init__(self):
        self.modules = ModuleNamespace(Slave().getmodule)
        self.builtin = self.modules.builtins

class Env(object):
    def __init__(self, servers=None, use_env=False):
        if use_env and 'ZERO_DEPLOY_SERVERS' in os.environ:
            _servers = os.environ['ZERO_DEPLOY_SERVERS']
            if len(_servers) > 0:
                servers = _servers.split(',')
        self.servers = self._load_config(servers)

    def _load_config(self, servers):
        if servers is not None:
            if type(servers) is not list:
                if type(servers) is tuple:
                    servers = list(servers)
                else:
                    servers = [servers]
        else:
            servers = ['local']

        path = P.expanduser("~/.zero_deploy.yaml")
        if P.exists(path):
            with open(path, 'r') as stream:
                try:
                    data = yaml.load(stream)
                    data = {d['host']: d for d in data}
                    if 'local' not in data.keys():
                        data['local'] = {'host': 'local'}
                except yaml.YAMLError:
                    data = {'local' : {'host': 'local'}}
        else:
            data = {'local' : {'host': 'local'}}

        servers_ops = []
        for target in servers:
            conf = data[target]
            host = conf.get('host', None)
            if host is None:
                continue
            
            if host == 'local':
                server = LocalMachine()
            else:
                mach = SshMachine(
                    host,
                    user=conf.get('user', None),
                    port=conf.get('port', None),
                    keyfile=conf.get('keyfile', None),
                    password=conf.get('password', None)
                )
                print('python_executable', conf.get('python_executable', None))
                server = DeployedServer(mach, python_executable=conf.get('python_executable', None))
                
            servers_ops.append(server)
        return servers_ops

    def __del__(self):
        self.close()
    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()
    def __iter__(self):
        return iter(self.servers)
    def __len__(self):
        return len(self.servers)
    def __getitem__(self, index):
        return self.servers[index]

    def close(self):
        while self.servers:
            s = self.servers.pop(0)
            s.close()

    def connect(self):
        connections = []
        for s in self.servers:
            c = s.classic_connect()
            c.modules.sys.stdout = sys.stdout
            connections.append(c)
        return connections if len(connections) > 1 else connections[0]

def remote_print(conn, *args):
    _print = "%s\n" % ( " ".join([str(p) for p in args]) )
    conn.modules.sys.stdout.write(_print)
    conn.modules.sys.stdout.flush()

#def using_package()


env = Env