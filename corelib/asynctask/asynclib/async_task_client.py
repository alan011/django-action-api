from django.conf import settings
from tornado import gen, tcpclient
from .defaults import ASYNCTASK_BIND_ADDR, ASYNCTASK_BIND_PORT
import json

HEADER_PREFIX = 'DataLength:'
HEADER_LENTGH = 24


class ClientResultException(Exception):
    def __init__(self, err=None):
        self.err = "ERROR: Result from AsyncTaskServer is not OK!" if err is None else err

    def __str__(self):
        return self.err


class ClientRunningException(Exception):
    def __init__(self, err=None):
        self.err = "ERROR: Some error happened when running async client." if err is None else err

    def __str__(self):
        return f"{self.err}"


class AsyncClient(object):
    def __init__(self, server_addr=None, server_port=None):
        self.server_addr = ASYNCTASK_BIND_ADDR if server_addr is None else server_addr
        self.server_port = ASYNCTASK_BIND_PORT if server_port is None else server_port

    def pack(self, msg):
        """
        To transfer string msg to bytes with fixed 24Bytes Header.

        :msg    A string to pack.

        Return a result tuple: '(None, err)' or '(<packed_value>, None)'.
        """
        value_len_max = HEADER_LENTGH - len(HEADER_PREFIX)
        header_value = str(len(msg) + HEADER_LENTGH)
        value_len = len(header_value)
        if value_len > value_len_max:
            return None, "Socket Data Packing Error: Data is too big!"
        header_value = '0' * (value_len_max - value_len) + header_value

        return (HEADER_PREFIX + header_value + msg).encode('utf-8'), None

    async def go(self, uuid, name, module, tracking=False, delaytime=0, *args, **kwargs):
        """
        To send serialized func data to AsyncTaskServer.

        :uuid       Task uuid.
        :name       function name. For dynamic import in AsyncTaskServer.
        :module     python module the function in. For dynamic import in AsyncTaskServer.
        :tracking   Record in backend database or Not.
        :delay      To run this task after `delay` seconds in AsyncTaskServer.

        `args` and `kwargs` are parameters for task function.

        Return None or err.
        """
        # To make bytes data.
        data = {
            'uuid': uuid,
            'name': name,
            'module': module,
            'tracking': tracking,
            'delaytime': delaytime,
            'args': args,
            'kwargs': kwargs
        }
        data_str = json.dumps(data)
        data_bytes, err = self.pack(data_str)
        if err is not None:
            raise ClientRunningException(f'ERROR: Client data_bytes packing failed: {err}')

        # Send data and handle result.
        count = 0
        stream = None
        while count < 3:
            count += 1
            try:
                stream = await tcpclient.TCPClient().connect(self.server_addr, self.server_port)
                break
            except Exception:
                await gen.sleep(3)
        if stream is None:
            raise ClientRunningException(f"Failed to connect to server. server_addr: {self.server_addr}, server_port: {self.server_port}")
        await stream.write(data_bytes)
        ret = await stream.read_bytes(256, partial=True)
        ret_str = ret.decode('utf-8')
        if ret_str != 'OK':
            raise ClientResultException(ret_str)

        stream.close()

    def record(self, uuid, name):
        """
        To record async task into backend database.

        :uuid   task uuid.
        :name   a task readable name.

        Return None or err.
        """
        if 'corelib.asynctask.api' in settings.INSTALLED_APPS:
            from corelib.asynctask.api.models import AsyncTask
            try:
                _, created = AsyncTask.objects.get_or_create(uuid=uuid, name=name)
            except Exception as e:
                return str(e)
            else:
                if not created:
                    return "UUID_EXIST"
