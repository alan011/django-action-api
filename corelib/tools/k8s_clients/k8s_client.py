import requests


class K8SClient(object):
    """
    适合自建的私有k8s集群，要求：
        1、认证走'bearer token'
        2、项目部署采用deployment + service + ingress的方式。
    """

    def __init__(self, k8s_api_url_base, k8s_bearer_token, namespace, name, service_name=None, ingress_name=None, *arg, **kwargs):
        self.url_base = k8s_api_url_base
        self.namespace = namespace
        self.deployment_name = name
        self.bearer_token = k8s_bearer_token
        self.service_name = service_name
        self.ingress_name = ingress_name

        # 变量拼接
        self.header_base = {"Authorization": "Bearer " + self.bearer_token}
        self.url_dp_create = f"{k8s_api_url_base}/apis/apps/v1/namespaces/{namespace}/deployments"
        self.url_dp_object = f"{k8s_api_url_base}/apis/apps/v1/namespaces/{namespace}/deployments/{name}"
        self.url_dp_status = f"{k8s_api_url_base}/apis/apps/v1/namespaces/{namespace}/deployments/{name}/status"
        self.last_generation = None

    def get_deployment(self, check_existence=False):
        res = requests.get(url=self.url_dp_object, headers=self.header_base, verify=False)
        print(f"get_deployment(): K8S API Response status code: {res.status_code}")
        # print(f"get_deployment(): K8S API Response status text: {res.text}")
        if res.status_code != 200:
            if check_existence and res.status_code == 404:
                return '__NOT_EXIST__'
            else:
                raise Exception(f"ERROR: Failed to get deployment object '{self.deployment_name}'. K8S API returns status Code: {res.status_code}")
        return res.json()

    def get_deployment_status(self):
        res = requests.get(url=self.url_dp_status, headers=self.header_base, verify=False)
        print(f"get_deployment_status(): K8S API Response status code: {res.status_code}")
        # print(f"get_deployment_status(): K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get deployment status of '{self.deployment_name}'. K8S API returns status Code: {res.status_code}")
        data = res.json()
        if 'metadata' in data:
            if 'managedFields' in data['metadata']:
                data['metadata'].pop('managedFields')
        return data

    def apply_deployment(self, deployment):
        # 检查deployment数据
        if not isinstance(deployment, dict):
            raise Exception("ERROR: Invalid deployment data. It must be a Dict.")
        if deployment.get('kind') != 'Deployment':
            raise Exception("ERROR: Invalid deployment data. Not a Deployment kind.")
        if not (isinstance(deployment.get('metadata'), dict) and deployment['metadata'].get('name') == self.deployment_name):
            raise Exception("ERROR: Invalid deployment data. Name not match.")

        # 存在就做patch，否则做create
        deployment_online = self.get_deployment(check_existence=True)
        method = 'POST' if deployment_online == '__NOT_EXIST__' else 'PATCH'
        url = self.url_dp_create if deployment_online == '__NOT_EXIST__' else self.url_dp_object
        headers = {"Content-Type": "application/strategic-merge-patch+json"} if method == 'PATCH' else {}
        headers.update(self.header_base)

        res = requests.request(method=method, url=url, headers=headers, json=deployment, verify=False)
        print(f"apply_deployment(): K8S API Response status code: {res.status_code}")
        # print(f"apply_deployment(): K8S API Response status text: {res.text}")
        if res.status_code != 200 and res.status_code != 201 and res.status_code != 202:
            raise Exception(f"ERROR: Failed to apply deployment '{self.deployment_name}'. K8S API returns status_code: {res.status_code}")

    def apply_service(self, service):
        pass

    def apply_ingress(self, ingress):
        pass

    def apply(self, deployment, service=None, ingress=None):
        """
        用于部署一个新的项目，需包含deployment, service, ingress等对象的spec配置数据。

        参数：
            deployment: 字典，描述deployment对象的spec配置数据。
            service: 字典，描述service对象的spec配置数据。
            ingress: 字典，描述ingress对象的spec配置数据。
        """
        self.apply_deployment(deployment)
        if isinstance(service, dict):
            self.apply_service(service)
        if isinstance(ingress, dict):
            self.apply_ingress(ingress)

    def set_image(self, target_image, containers, strategy=None):
        """
        执行rolling_update

        参数：
            containers  一个列表，元素为一个字典。
                        字典描述了一个pod中的container该如何更新镜像。字典需包含两个字段:
                            'name': pod中容器的名称
                            'image': 该容器需更新的目标镜像
            strategy    更新策略。
        """
        # get generation.
        obj_data = self.get_deployment()
        self.last_generation = obj_data['metadata'].get('generation', 0)

        # set containers
        _containers = []
        for c in containers:
            _containers.append({
                'name': c,
                'image': target_image
            })

        # make body
        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": _containers
                    }
                },
                # 'Strategy': {
                #     "type": "RollingUpdate",
                #     "rollingUpdate": {
                #         "maxUnavailable": 50
                #     }
                # }
            }
        }

        # 发起请求，分析结果
        headers = {"Content-Type": "application/strategic-merge-patch+json"}
        headers.update(self.header_base)
        res = requests.patch(url=self.url_dp_object, headers=headers, json=body, verify=False)
        print(f"set_image(): K8S API Response status code: {res.status_code}")
        print(f"set_image(): K8S API Response status text: {res.text}")
        if res.status_code != 200:
            raise Exception(f"ERROR: set_image failed. API returns status code: {res.status_code}")

    def get_updating_progress(self):
        if self.last_generation is None:
            raise Exception("`self.last_generation` is not set as expected!")
        status = self.get_deployment_status()
        this_generation = int(status['status'].get('observedGeneration', 0))
        replicas = int(status['spec'].get('replicas', 0))
        updated = int(status['status'].get('updatedReplicas', 0)) if this_generation > self.last_generation else 0
        return updated, replicas

    def delete_deployment(self):
        res = requests.delete(url=self.url_dp_object, headers=self.header_base, verify=False)
        print(f"delete_deployment(): K8S API Response status code: {res.status_code}")
        # print(f"delete_deployment(): K8S API Response status text: {res.text}")
        if res.status_code != 200 and res.status_code != 202:
            raise Exception(f"ERROR: delete_deployment failed. API returns status code: {res.status_code}")
