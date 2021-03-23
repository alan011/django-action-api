import requests


class K8SClientBase(object):
    """
    仅适用于k8s-apiserver的直接认证调用。

    对于各大云厂商的接口网关复杂认证方式，并不适用。
    """

    def __init__(self, api_url_base, auth_params, auth_type=None, api_version_prefix=None, ignore_https_verify=False, *args, **kwargs):
        '''
        确定认证用的headers，以及与k8s-apiserver接口版本相关的基础url。

        参数：
            api_url_base        字符串。如：'http://<ip>:<port>', 'https://<domain_name>'

            auth_type           可选范围：'Bearer Token', 'CA Certs';
                                默认为'Bearer Token'。

            auth_params         一个字典。记录的参数，用于传k8s接口认证。字典字段要求，随`auth_type`，有不同要求。
                                'Bearer Token'，要求：{'bearer_token': '<a bearer token string>'}
                                'CA Certs'，要求：{

                                }

            api_version_prefix  一个字符串。k8s-apiserver的版本前缀，用于资源域名拼接。
                                默认为：/apis/apps/v1
                                老版本的k8s还可能是/apis/extensions/v1beta1
            ignore_https_verify Bool类型。用于API调用时，对私有k8s集群，忽略https证书校验。

        '''
        self.api_url_base = str(api_url_base)
        self.auth_params = auth_params
        self.auth_type = 'Bearer Token' if auth_type is None else auth_type
        self.api_version_prefix = '/apis/apps/v1' if api_version_prefix is None else str(api_version_prefix)

        # 设置接口认证参数
        self.headers = {}
        self.request_verify = None
        self.certs = None
        if self.auth_type == 'Bearer Token':
            if 'bearer_token' not in self.auth_params:
                raise Exception(f"K8SClientBase.__init__(): '{self.auth_type}' requires 'bearer_token' in arg `auth_params`!")
            self.headers = {"Authorization": "Bearer " + self.auth_params['bearer_token']}
            if ignore_https_verify:
                self.request_verify = False
        elif self.auth_type == 'CA Certs':
            for key in ['cert_file', 'cert_key_file']:
                if key not in self.auth_params:
                    raise Exception(f"K8SClientBase.__init__(): '{self.auth_type}' requires '{key}' in arg `auth_params`!")
            self.request_verify = self.auth_params['ca_file'] if 'ca_file' in self.auth_params else False
            self.certs = (self.auth_params['cert_file'], self.auth_params['cert_key_file'])
        else:
            raise Exception(f"K8SClientBase.__init__(): Invalid auth_type '{auth_type}'!")

        # 拼接API基础URL
        if self.api_url_base.endswith('/'):
            self.api_url_base = self.api_url_base[:-1]
        if not self.api_version_prefix.startswith('/'):
            self.api_version_prefix = '/' + self.api_version_prefix
        if self.api_version_prefix.endswith('/'):
            self.api_version_prefix = self.api_version_prefix[:-1]
        self.api_url = f"{self.api_url_base}{self.api_version_prefix}"

    def call(self, method, url, data=None, additional_headers=None):
        """
        封装认证过程，统一发起k8s接口调用。
        """
        headers = {}
        headers.update(self.headers)
        method = method.upper()
        if method == 'PATCH':
            headers.update({"Content-Type": "application/strategic-merge-patch+json"})
        if isinstance(additional_headers, dict):
            headers.update(additional_headers)

        request_params = {
            'method': method,
            'url': url,
            'headers': headers,
        }

        if isinstance(data, dict):
            request_params['json'] = data

        if self.request_verify is not None:
            request_params['verify'] = self.request_verify

        if self.auth_type == 'CA Certs':
            request_params['cert'] = self.certs

        return requests.request(**request_params)
