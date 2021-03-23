from .client_base import K8SClientBase
from datetime import datetime


class DaemonsetClient(K8SClientBase):
    """
    用于daemonset增删改查。

    通常用于daemonset的部署与发版。
    """

    def __init__(self, name, namespace, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemonset_name = name
        self.namespace = namespace

        # 变量拼接
        self.url_ds_base = f"{self.api_url}/namespaces/{namespace}/daemonsets"
        self.url_ds_object = f"{self.api_url}/namespaces/{namespace}/daemonsets/{name}"
        self.last_generation = None

    def get_daemonset(self, check_existence=False):
        """
        获取daemonset对象
        """
        _pre = "DaemonsetClient.get_daemonset()"

        # 直接请求数据
        res = self.call(method='get', url=self.url_ds_object)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        if res.status_code != 200:
            if check_existence and res.status_code == 404:
                return '__NOT_EXIST__'
            else:
                raise Exception(f"{_pre} [ERROR]: Failed to get daemonset object '{self.daemonset_name}'. K8S API returns status Code: {res.status_code}")

        return res.json()

    def get_daemonset_status(self):
        """
        单独获取daemonset的status
        """
        data = self.get_daemonset()
        if 'metadata' in data:
            if 'managedFields' in data['metadata']:
                data['metadata'].pop('managedFields')
        return data

    def apply(self, daemonset):
        """
        相当于kubectl的apply功能

        参数：
            daemonset      一个字典。包含daemonset的所有定义参数。
        """
        _pre = "DaemonsetClient.apply()"

        # 检查daemonset数据
        if not isinstance(daemonset, dict):
            raise Exception(f"{_pre} [ERROR]: Invalid daemonset data. It must be a Dict.")
        if daemonset.get('kind') != 'Daemonset':
            raise Exception(f"{_pre} [ERROR]: Invalid daemonset data. Not a Daemonset kind.")
        if not (isinstance(daemonset.get('metadata'), dict) and daemonset['metadata'].get('name') == self.daemonset_name):
            raise Exception(f"{_pre} [ERROR]: Invalid daemonset data. Name not match.")

        # 存在就做patch，否则做create
        daemonset_online = self.get_daemonset(check_existence=True)
        method = 'POST' if daemonset_online == '__NOT_EXIST__' else 'PATCH'
        url = self.url_ds_base if daemonset_online == '__NOT_EXIST__' else self.url_ds_object

        # 发起请求
        res = self.call(method=method, url=url, data=daemonset)
        print(f"{_pre} [ERROR]: K8S API Response status code: {res.status_code}")
        if res.status_code != 200 and res.status_code != 201 and res.status_code != 202:
            raise Exception(f"{_pre} [ERROR]: Failed to apply daemonset '{self.daemonset_name}'. K8S API returns status_code: {res.status_code}")

    def _set_maxunavailable(self, data, desiredNumber, deploy_proportion, max_unavailable):
        # 计算maxUnavailable
        _max = None
        if max_unavailable:
            _max = max_unavailable
        elif deploy_proportion:
            _max = int(desiredNumber / deploy_proportion)
            if _max < 1:
                _max = 1
        if _max:
            data['spec']['updateStrategy'] = {
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

            当deploy_proportion与max_unavailable同时存在时，以max_unavailable为准
        """
        _pre = 'DaemonsetClient.set_image()'

        # 检查containers
        if not isinstance(containers, list):
            raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, must be a list.")
        for c in containers:
            if not isinstance(c, dict):
                raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, item must be a dict.")
            if 'name' not in c or 'image' not in c:
                raise Exception(f"{_pre} [ERROR]: Illigal Arg `containers`, illegal item.")

        # 获取generation.
        obj_data = self.get_daemonset()
        self.last_generation = obj_data['metadata'].get('generation', 0)
        desiredNumber = obj_data['status']['desiredNumberScheduled']

        # request data
        data = {"spec": {"template": {"spec": {"containers": containers}}}}
        self._set_maxunavailable(data, desiredNumber, deploy_proportion, max_unavailable)

        # 发起请求，分析结果
        res = self.call(method='patch', url=self.url_ds_object, data=data)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        print(f"{_pre}: K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"{_pre} [ERROR]: To set image failed. API returns status code: {res.status_code}")

    def patch_version(self, version=None, deploy_proportion=None, max_unavailable=None):
        """
        一般用于重启daemonset中的pod。也适用于依赖initContainer来更新部署应用程序的情况。
        """
        _pre = "DaemonsetClient.patch_version()"

        version_date_suffix = datetime.now().strftime("patch-at-%Y%m%d_%H%M%S")
        version = version_date_suffix if version is None else f"{str(version)}.{version_date_suffix}"

        # 获取generation.
        obj_data = self.get_daemonset()
        self.last_generation = obj_data['metadata'].get('generation', 0)
        desiredNumber = obj_data['status']['desiredNumberScheduled']

        # request data
        data = {"spec": {"template": {"metadata": {"labels": {"version": version}}}}}
        self._set_maxunavailable(data, desiredNumber, deploy_proportion, max_unavailable)

        # 发起请求，分析结果
        res = self.call(method='patch', url=self.url_ds_object, data=data)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        print(f"{_pre}: K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"{_pre} [ERROR]: To patch version failed. API returns status code: {res.status_code}")

    def get_updating_progress(self):
        """
        用于获取更新部署时，更新进度。
        """
        _pre = 'DaemonsetClient.get_updating_progress()'
        if self.last_generation is None:
            raise Exception(f"{_pre} [ERROR]: `self.last_generation` is not set.")
        data = self.get_daemonset()
        this_generation = data['status'].get('observedGeneration', 0)
        updated = data['status'].get('updatedNumberScheduled', 0) if this_generation > self.last_generation else 0
        desired = data['status'].get('desiredNumberScheduled', 0)
        ready = data['status'].get('numberReady', 0)

        if updated <= ready:
            return updated, desired
        else:
            return ready, desired

    def delete_daemonset(self):
        """
        用于删除daemonset
        """
        _pre = 'DaemonsetClient.delete_daemonset()'
        res = self.call(method='delete', url=self.url_ds_object)
        print(f"{_pre}: K8S API Response status code: {res.status_code}")
        if res.status_code != 200 and res.status_code != 202:
            raise Exception(f"{_pre} [ERROR]: To delete daemonset failed. API returns status code: {res.status_code}")
