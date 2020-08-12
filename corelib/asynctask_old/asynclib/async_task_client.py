from corelib.asynctask.config import ASYNC_TASK_SOCKET
from django.conf import settings
import socket
import json

HEADER_PREFIX = 'DataLength:'
HEADER_LENTGH = 24


class ClientResultException(Exception):
    def __str__(self):
        return "Result from AsyncTaskServer is not OK!"


class AsyncTaskClient(object):
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

    def go(self, uuid, name, module, tracking, *args, **kwargs):
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
        # Init socket client, make bytes data.
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        data = {
            'uuid': uuid,
            'name': name,
            'module': module,
            'tracking': tracking,
            'args': args,
            'kwargs': kwargs
        }
        data_str = json.dumps(data)
        data_bytes, err = self.pack(data_str)
        if err is not None:
            return err

        # Send data and handle result.
        err = None
        try:
            client.connect(ASYNC_TASK_SOCKET)
            client.send(data_bytes)
            result = client.recv(16)  # Result data always is in choices of 'OK' or 'ERROR'.
            result_str = result.decode('utf-8')
            if result_str != 'OK':
                raise ClientResultException
        except Exception as e:
            err = str(e)

        # The end.
        client.close()
        return err

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
