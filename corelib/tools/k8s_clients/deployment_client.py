from .client_base import K8SClientBase
from datetime import datetime


class DeploymentClient(K8SClientBase):
    """
    用于deployment增删改查。

    通常用于deployment的部署与发版。

    目前，更新策略仅支持RollingUpdate。
    """

    def __init__(self, name, namespace, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deployment_name = name
        self.namespace = namespace

        # 变量拼接
        self.url_dp_base = f"{self.api_url}/namespaces/{namespace}/deployments"
        self.url_dp_object = f"{self.api_url}/namespaces/{namespace}/deployments/{name}"
        self.url_dp_status = f"{self.api_url}/namespaces/{namespace}/deployments/{name}/status"
        self.last_generation = None

    def get_deployment(self, check_existence=False):
        """
        获取deployment对象
        """
        _pre = "DeploymentClient.get_deployment()"

        # 直接请求数据
        res = self.call(method='get', url=self.url_dp_object)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        if res.status_code != 200:
            if check_existence and res.status_code == 404:
                return '__NOT_EXIST__'
            else:
                raise Exception(f"{_pre} [ERROR]: Failed to get deployment object '{self.deployment_name}'. K8S API returns status Code: {res.status_code}")

        return res.json()

    def get_deployment_status(self):
        """
        单独获取deployment的status
        """
        _pre = "DeploymentClient.get_deployment_status()"

        # 直接请求数据
        res = self.call(method='get', url=self.url_dp_status)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        if res.status_code != 200:
            raise Exception(f"{_pre} [ERROR]: Failed to get deployment status of '{self.deployment_name}'. K8S API returns status Code: {res.status_code}")

        data = res.json()
        if 'metadata' in data:
            if 'managedFields' in data['metadata']:
                data['metadata'].pop('managedFields')
        return data

    def apply(self, deployment):
        """
        相当于kubectl的apply功能

        参数：
            deployment      一个字典。包含deployment的所有定义参数。
        """
        _pre = "DeploymentClient.apply()"

        # 检查deployment数据
        if not isinstance(deployment, dict):
            raise Exception(f"{_pre} [ERROR]: Invalid deployment data. It must be a Dict.")
        if deployment.get('kind') != 'Deployment':
            raise Exception(f"{_pre} [ERROR]: Invalid deployment data. Not a Deployment kind.")
        if not (isinstance(deployment.get('metadata'), dict) and deployment['metadata'].get('name') == self.deployment_name):
            raise Exception(f"{_pre} [ERROR]: Invalid deployment data. Name not match.")

        # 存在就做patch，否则做create
        deployment_online = self.get_deployment(check_existence=True)
        method = 'POST' if deployment_online == '__NOT_EXIST__' else 'PATCH'
        url = self.url_dp_base if deployment_online == '__NOT_EXIST__' else self.url_dp_object

        # 发起请求
        res = self.call(method=method, url=url, data=deployment)
        print(f"{_pre} [ERROR]: K8S API Response status code: {res.status_code}")
        if res.status_code != 200 and res.status_code != 201 and res.status_code != 202:
            raise Exception(f"{_pre} [ERROR]: Failed to apply deployment '{self.deployment_name}'. K8S API returns status_code: {res.status_code}")

    def _set_maxunavailable(self, data, replicas, deploy_proportion, max_unavailable):
        # 计算maxUnavailable
        _max = None
        if max_unavailable:
            _max = max_unavailable
        elif deploy_proportion:
            _max = int(replicas / deploy_proportion)
            if _max < 1:
                _max = 1

        if _max:
            data['spec']['Strategy'] = {
                "type": "RollingUpdate",
                "rollingUpdate": {
                    "maxUnavailable": _max
                }
            }

    def set_image(self, containers, deploy_proportion=None, max_unavailable=None):
        """
        相当于kubectl的set image指令。

        参数：
            containers  一个列表，元素为一个字典。
                        字典描述了一个pod中的container该如何更新镜像。字典需包含两个字段:
                            'name': pod中容器的名称
                            'image': 该容器需更新的目标镜像
            deploy_proportion   int型，部署比例系数。如'3'，就表示每次部署1/3
            max_unavailable     int型，滚动更新实例个数。设置多少个，每次就更新多少个。

            注意，对于默认的‘RollingUpdate’策略，当deploy_proportion与max_unavailable同时存在时，以max_unavailable为准
        """
        _pre = 'DeploymentClient.set_image()'

        # 检查containers
        if not isinstance(containers, list):
            raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, must be a list.")
        for c in containers:
            if not isinstance(c, dict):
                raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, item must be a dict.")
            if 'name' not in c or 'image' not in c:
                raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, illegal item.")

        # 获取generation.
        obj_data = self.get_deployment()
        self.last_generation = obj_data['metadata'].get('generation', 0)
        replicas = obj_data['spec']['replicas']

        # request data
        data = {"spec": {"template": {"spec": {"containers": containers}}}}
        self._set_maxunavailable(data, replicas, deploy_proportion, max_unavailable)

        # 发起请求，分析结果
        res = self.call(method='patch', url=self.url_dp_object, data=data)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        print(f"{_pre}: K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"{_pre} [ERROR]: To set image failed. API returns status code: {res.status_code}")

    def patch_version(self, version=None, deploy_proportion=None, max_unavailable=None):
        """
        一般用于重启deployment中的pod。也适用于依赖initContainer来更新部署应用程序的情况。

        参数：
            version     一个字符串，表征指定的版本号。
                        若不指定，则默认为"patch-at-<当前日期时间>"
            deploy_proportion   int型，部署比例系数。如'3'，就表示每次部署1/3
            max_unavailable     int型，滚动更新实例个数。设置多少个，每次就更新多少个。

            注意，对于默认的‘RollingUpdate’策略，当deploy_proportion与max_unavailable同时存在时，以max_unavailable为准
        """
        _pre = "DeploymentClient.patch_version()"

        version_date_suffix = datetime.now().strftime("patch-at-%Y%m%d_%H%M%S")
        version = version_date_suffix if version is None else f"{str(version)}.{version_date_suffix}"

        # 获取generation.
        obj_data = self.get_deployment()
        self.last_generation = obj_data['metadata'].get('generation', 0)
        replicas = obj_data['spec']['replicas']

        # request data
        data = {"spec": {"template": {"metadata": {"labels": {"version": version}}}}}
        self._set_maxunavailable(data, replicas, deploy_proportion, max_unavailable)

        # 发起请求，分析结果
        res = self.call(method='patch', url=self.url_dp_object, data=data)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        print(f"{_pre}: K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"{_pre} [ERROR]: To patch version failed. API returns status code: {res.status_code}")

    def get_updating_progress(self):
        """
        用于获取更新部署时，更新进度。
        """
        _pre = 'DeploymentClient.get_updating_progress()'
        if self.last_generation is None:
            raise Exception(f"{_pre} [ERROR]: `self.last_generation` is not set as expected!")
        status = self.get_deployment_status()
        this_generation = int(status['status'].get('observedGeneration', 0))
        replicas = int(status['spec'].get('replicas', 0))
        updated = int(status['status'].get('updatedReplicas', 0)) if this_generation > self.last_generation else 0
        return updated, replicas

    def delete_deployment(self):
        """
        用于删除deployment
        """
        _pre = 'DeploymentClient.delete_deployment()'
        res = self.call(method='delete', url=self.url_dp_object)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        if res.status_code != 200 and res.status_code != 202:
            raise Exception(f"{_pre} [ERROR]: To delete deployment failed. API returns status code: {res.status_code}")
