import requests
import re


class SaltRunnerUsageERROR(Exception):
    pass


class SaltRunner:
    """
    通过调用salt-api来执行saltstack集中控制指令的工具。
    """
    saltapi_session = None

    def __init__(self, salt_api_url, salt_api_user, salt_api_passwd, eauth='pam'):
        """
        登录salt-api，获得session
        """
        self.salt_api_url = salt_api_url
        self.salt_api_auth_config = {
            'username': salt_api_user,
            'password': salt_api_passwd,
            'eauth': eauth,
        }

        salt_api_session = requests.Session()
        salt_api_session_auth = salt_api_session.post(salt_api_url + '/login', self.salt_api_auth_config, verify=False)
        if salt_api_session_auth.status_code != 200:
            raise Exception('ERROR: Login to salt-api failed. HTTP status: %d' % salt_api_session_auth.status_code)
        else:
            self.saltapi_session = salt_api_session
        self.result = None

    def go(self, node_list, system_cmd=None, script=None):
        """
        用于调用salt-api来远程一个命令，或者一个脚本。

        参数：
            node_list   一个列表，元素为ip字符串，代表要执行操作的目标机器。
            system_cmd  命令行字符串，远程执行的命令。
            script      字符串，表示saltstack可远程获取的脚本地址。
                        要求只能传入http开头的url，或者salt开头的存放于saltstack fileroot中的文件
        """
        # 解析参数
        nodes = ','.join(node_list)
        if system_cmd is not None:
            salt_func = 'cmd.run_all'
        elif script is not None:
            salt_func = 'cmd.script'
            if re.search('^(http|salt).*://.*', script) is None:
                raise SaltRunnerUsageERROR(f"ERROR: saltstack cannot get remote script with content: {script}")
        else:
            raise SaltRunnerUsageERROR("ERROR: Params `system_cmd` or `script` must be provided.")

        salt_api_action = {"client": "local",
                           "tgt": nodes,
                           "fun": salt_func,
                           "arg": system_cmd if system_cmd else script,
                           "expr_form": "list"}   # To make salt api called like system cmd: "salt -L node1,node2 ...."

        # 发起salt-api调用，获取调用结果
        res = self.saltapi_session.post(self.salt_api_url, salt_api_action, verify=False)
        if res.status_code != 200:
            print(res.text)
            raise Exception(f"ERROR: Failed to call salt-api. status_code: {res.status_code}.")
        self.result = res.json()['return'][0]
