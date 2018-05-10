"""
Enviroment is the core of zero_deploy package. It control when and how modules will be used, loading configuration
and local machine enviroment variable.
"""
from plumbum import SshMachine
import rpyc
from rpyc.utils.zerodeploy import DeployedServer
from rpyc.core.service import ModuleNamespace, Slave

import yaml
import os
import os.path as P
import sys

class LocalMachine:
    """ Mock remote machine as local machine. Returns 'LocalEnv' when a connection are made.
    """
    def classic_connect(self):
        return LocalEnv()
    
    def close(self):
        pass

class LocalEnv:
    """ Use local machine as fallback if no configurations are found.
    """
    def __init__(self):
        self.modules = ModuleNamespace(Slave().getmodule)
        self.builtin = self.modules.builtins

class Env(object):
    """ Enviroment mananger will control the actual enviroment at runtime. It load `~/.zero_deploy.yaml` configuration
    if avaliable and parse the list of configurations. Alos allow use enviroment variable `ZERO_DEPLOY_SERVERS` to
    choose which server's the connection will be made.
    """
    def __init__(self, servers=None, use_env=False):
        """ If no servers or enviroment variable are found the local machine will be the default Env. 
        Params:
        - servers: can be one or multiple `host` avaliable on configuration file. If more than one is provided then
        multiples connections when call `connect`.
        - use_env: if True will try use `ZERO_DEPLOY_SERVERS` local enviroment variable, if that enviroment variable are
        not avaliable will fallback to `servers` params.
        """
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
    """
    Use remote and local sys.stdout.
    """
    _print = "%s\n" % ( " ".join([str(p) for p in args]) )
    conn.modules.sys.stdout.write(_print)
    conn.modules.sys.stdout.flush()

def remote_import(conn, modules, package=None):
    """
    Import remote module, if remote don't have the module the local module will be uploaded safely to remote.
    """
    if type(modules) is not dict and type(modules) is not list:
        modules = [modules]
    
    imported_modules = []
    for module in modules:
        if package is not None:
            import_module = ".".join([package, module])
        else:
            import_module = module
        try:
            imported_module = conn.modules[import_module]
        except ModuleNotFoundError:
            _import_module = __import__(import_module)
            rpyc.utils.classic.upload_module(conn, _import_module, import_module)
            imported_module = conn.modules[import_module]
        
        imported_modules.append(imported_module)
    
    return imported_modules[0] if len(imported_modules) == 1 else imported_modules


env = Env