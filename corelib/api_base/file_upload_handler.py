import os
from django import forms
from corelib.tools.func_tools import genUUID
from django.utils import timezone
from random import randint


class UploadFileForm(forms.Form):
    file = forms.FileField()


class FileUploader(object):
    """
    文件上传handler工具，需要在View请求处理函数中使用。

    用法举例：
    ```python

    from django.http import HttpResponse
    from django.views.generic import View
    from django.views.decorators.csrf import csrf_exempt
    from django.utils.decorators import method_decorator
    from corelib import FileUploader
    import json

    @method_decorator(csrf_exempt, name='dispatch')
    class imageUploader(View):
        def post(self, request, *args, **kwargs):
            handler = FileUploader(request)
            handler.receiveFile()
            if not handler.result:
                return HttpResponse(handler.error_message, status=handler.http_status)
            return HttpResponse(json.dumps(handler.result_data), content_type='application/json')

    ```
    注意，以上示例没有做权限验证，任何人都可通过此接口上传文件，不可用作生产环境。
    """

    def __init__(self, request, storage_base=None, storage_hash_type=None, filename_suffix_limit=None, keep_origin_filename=None, *args, **kwargs):
        """
        关于文件存储路径的设置属性：

        storage_base        本地存储根目录，要求绝对路径。默认值为'/tmp'
                            任何非法的设置，都会导致启用默认值。

        storage_hash_type   在storage_base存储根目录下，自动生成多级hash目录存储。
                            默认为None，表示不做多级目录存储，直接存储在storage_base目录下。
                            支持两种类型: 'number', 'date'
                            - number: 表示随机自动生成1~255的三层存储目录。
                                例如：存储一个图片，'/tmp/2/255/10/test.png'
                            - date: 表示根据当前日期生成三级存储目录。
                                例如：存储一个图片，'/tmp/2021/04/06/test.png'

        关于文件类型限制的设置属性：
        （注意：目前只能从上传的文件名上做文件类型检查，无法从文件内容上做实际检查！）

        file_format_limits  是一个可以做in判断的数据对象，要求其元素为字符串，字母都需要小写。（列表，元组，集合都可）。
                            默认为None，表示不做限制。
                            例如：要限制只接受png，jpg格式的图片，可以设置为 ['png', 'jpg']

        若有无法满足需求的地方，请在继承此class时，重载这里的方法。

        其他设置属性：

        keep_origin_filename    若为True则保留源文件的的文件名称。否则生成一个64位的随机文件名（默认）。
        """
        self.request = request

        # 行为控制属性
        self.storage_base = storage_base
        self.storage_hash_type = storage_hash_type
        self.filename_suffix_limit = filename_suffix_limit
        self.keep_origin_filename = keep_origin_filename

        # 处理结果
        self.result = True
        self.message = ''
        self.error_message = ''
        self.http_status = 200
        self.result_data = None

    def error(self, error_message, http_status=400, return_value=None):
        """
        当处理失败时，设置error的便捷方法
        """
        self.result = False
        self.error_message += error_message
        self.http_status = http_status
        return return_value

    def makeStoragePath(self):
        # 检查基础设置
        self.storage_base = str(self.storage_base)
        if not self.storage_base or not self.storage_base.startswith('/'):
            self.storage_base = '/tmp'

        # 创建存储跟目录
        if not os.path.isdir(self.storage_base):
            try:
                os.makedirs(self.storage_base)
            except Exception as e:
                self.error(f"ERROR: Failed create storage base dir: {self.storage_base}. {str(e)}", http_status=500)

        # 创建多级存储目录
        path = self.storage_base
        if self.storage_hash_type == 'number':
            for i in range(3):
                path = os.path.join(path, randint(1, 255))
        elif self.storage_hash_type == 'date':
            _now = timezone.now()
            s_year = _now.strftime('%Y')
            s_month = _now.strftime('%m')
            s_day = _now.strftime('%d')
            path = os.path.join(path, s_year, s_month, s_day)
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except Exception as e:
                self.error(f"ERROR: Failed create storage path: {path}. {str(e)}", http_status=500)

        return path

    def checkFileFormat(self, upload_file_name):
        """
        注意：只能从上传的文件名上做文件类型检查，无法从文件内容上做实际检查！
        """
        if self.filename_suffix_limit:
            tmp = upload_file_name.split('.')
            if len(tmp) < 2:
                return self.error(f"ERROR: Invalid file received: '{upload_file_name}'.", http_status=400)
            suffix = tmp[-1]
            if suffix.lower() not in self.filename_suffix_limit:
                return self.error(f"ERROR: Unsupported file format: '.{suffix}'.", http_status=400)
            return suffix

    def receiveFile(self):
        # 检查文件格式
        upload_file_name = str(self.request.FILES['file'])
        suffix = self.checkFileFormat(upload_file_name)
        if not self.result:
            return None

        # 创建存储目录
        storage_path = self.makeStoragePath()
        if not self.result:
            return None

        # make file storage full path
        if self.keep_origin_filename:
            file_path = os.path.join(storage_path, upload_file_name)
        else:
            uuid = genUUID(64)
            file_path = os.path.join(storage_path, f'{uuid}.{suffix}')
            while os.path.isfile(file_path):
                uuid = genUUID(64)
                file_path = os.path.join(storage_path, f'{uuid}.{suffix}')

        # Read file content and save it.
        form = UploadFileForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            with open(file_path, 'wb+') as f:
                for chunk in self.request.FILES['file'].chunks():
                    f.write(chunk)
            self.result_data = {
                'result': 'SUCCESS',
                'message': 'To upload file succeeded.',
                'file_path': file_path
            }
        else:
            self.error('ERROR: Invalid file uploading post.', http_status=400)
