import requests
import re


class SaltRunnerUsageERROR(Exception):
    pass


class SaltRunner:
    """
    通过调用salt-api来执行saltstack集中控制指令的工具。
    """
    saltapi_session = None

    def __init__(self, salt_api_url, salt_api_user, salt_api_passwd, eauth='pam', quiet=False):
        """
        登录salt-api，获得session
        """
        self.salt_api_url = salt_api_url
        self.salt_api_auth_config = {
            'username': salt_api_user,
            'password': salt_api_passwd,
            'eauth': eauth,
        }

        self.quiet = quiet
        salt_api_session = requests.Session()
        salt_api_session_auth = salt_api_session.post(salt_api_url + '/login', self.salt_api_auth_config, verify=False)
        if salt_api_session_auth.status_code != 200:
            raise Exception('SaltRunner.__init__(): ERROR: Login to salt-api failed. HTTP status: %d' % salt_api_session_auth.status_code)
        else:
            self.saltapi_session = salt_api_session
        self.result = {}

    def go(self, node_list, system_cmd=None, script=None, script_args=None):
        """
        用于调用salt-api来远程一个命令，或者一个脚本。

        参数：
            node_list   一个列表，元素为ip字符串，代表要执行操作的目标机器。
            system_cmd  命令行字符串，远程执行的命令。
            script      字符串，表示saltstack可远程获取的脚本地址。
                        要求只能传入http开头的url，或者salt开头的存放于saltstack fileroot中的文件
            script_args 要求是一个list，每个元素会自动转化为字符串，将作为脚本的位置参数。
                        注意：
                        a.如果参数包含空格，则会自动给参数加上"'"；
                        b.如果参数包含空格与引号：包含双引号，则外围会使用单引号"'"；包含单引号，则外围会使用双引号'"'，如果单双引号都有，则抛错。

        """
        # 解析参数
        nodes = ','.join(node_list)
        if system_cmd is not None:
            salt_func = 'cmd.run_all'
        elif script is not None:
            salt_func = 'cmd.script'
            if re.search('^(http|salt).*://.*', script) is None:
                raise SaltRunnerUsageERROR(f"SaltRunner.go(): ERROR: saltstack cannot get remote script with content: {script}")
        else:
            raise SaltRunnerUsageERROR("SaltRunner.go(): ERROR: Params `system_cmd` or `script` must be provided.")

        salt_api_action = {
            "client": "local",
            "tgt": nodes,
            "fun": salt_func,
            "arg": system_cmd if system_cmd else script,
            "expr_form": "list"
        }   # To make salt api called like system cmd: "salt -L node1,node2 ...."
        if script_args:
            if not isinstance(script_args, list):
                raise SaltRunnerUsageERROR(f"SaltRunner.go(): ERROR: `script_args` must be a list.")

            # 给包含空字符的参数，加上引号。
            args = ''
            for arg in script_args:
                _arg = str(arg)
                if re.search(r'\s', _arg):
                    if not ((_arg.startswith('"') and _arg.endswith('"')) or (_arg.startswith("'") and _arg.endswith("'"))):
                        if re.search(r'"', _arg) and re.search(r"'", _arg):
                            raise Exception("SaltRunner.go(): ERROR: SaltRunner cannot handle complex script args which contains both `'` and `\"`.")
                        elif re.search(r'"', _arg):
                            _arg = f"'{_arg}'"
                        else:
                            _arg = f'"{_arg}"'
                args += _arg
                args += ' '
            salt_api_action['arg'] = [salt_api_action['arg'], args]

        # 发起salt-api调用，获取调用结果
        res = self.saltapi_session.post(self.salt_api_url, salt_api_action, verify=False)
        if res.status_code != 200:
            if not self.quiet:
                print(res.text)
            raise Exception(f"SaltRunner.go(): ERROR: Failed to call salt-api. status_code: {res.status_code}.")
        self.result.update(res.json()['return'][0])
