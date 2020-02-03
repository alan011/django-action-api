from corelib.tools.logger import Logger
from corelib.asynctask.config import (
    # ASYNC_TASK_LOGDIR,
    # ASYNC_TASK_LOGFILE_PREFIX,
    # ASYNC_TASK_WORKERS,
    ASYNC_TASK_LOG_LEVEL,
    ASYNC_TASK_REGISTER_MODULE,
    ASYNC_TASK_SOCKET)
from multiprocessing import Pool
from .async_task_client import HEADER_LENTGH
import socket
import os
import time
import json
from django.conf import settings
from importlib import import_module


class AsyncTaskServer(object):
    def __init__(self):
        self.sock = ASYNC_TASK_SOCKET
        self.pool = []
        self.funcs = {}

    def registerFunctions(self):
        logger = Logger(msg_prefix='AsyncTaskServer.registerFunctions(): ', trigger_level=ASYNC_TASK_LOG_LEVEL)
        for app in settings.INSTALLED_APPS:
            mod_str = f'{app}.{ASYNC_TASK_REGISTER_MODULE}'
            try:
                mod = import_module(mod_str)
            except Exception:
                logger.log(f"Ignore invalid django-installed app: '{app}'.", level='DEBUG')
            else:
                for attr_name in filter(lambda a: not a.startswith('_'), dir(mod)):
                    func = getattr(mod, attr_name)
                    if getattr(func, 'is_asynctask', False):
                        index = f'{mod_str}.{attr_name}'
                        self.funcs[index] = func
                        logger.log(f"To register asynctask funcion '{index}' succeeded.")

    def asyncRun(self, uuid, name, module, tracking, *args, **kwargs):
        """
        To run a func asynchronously with `*args` and `**kwargs`
        """
        # logger = Logger(msg_prefix='AsyncTaskServer.asyncRun(*): ', trigger_level=ASYNC_TASK_LOG_LEVEL)
        index = f'{module}.{name}'
        func = self.funcs[index]
        res = func()
        print(res)
        print("asyncRun not finished.")
        pass

    def worker(self, connection):
        logger = Logger(msg_prefix='AsyncTaskServer.worker(): ', trigger_level=ASYNC_TASK_LOG_LEVEL)

        # receive data from client. Parse json data.
        try:
            chunk_len = 8196
            data_b = connection.recv(chunk_len)
            header = data_b[:HEADER_LENTGH]
            data_len = int(header.decode('utf-8').split(':')[1])
            while len(data_b) < data_len:
                data_b = connection.recv(chunk_len)
            data = json.loads(data_b[HEADER_LENTGH:].decode('utf-8'))
            # logger.log(f"New task received: {str(data)}", level="INFO")
            result = 'OK'
        except Exception as e:
            logger.log(str(e), level="ERROR")
            result = 'ERROR'
        connection.send(result.encode('utf-8'))

        # To run task.
        if result == 'OK':
            uuid, name, module, tracking = data['uuid'], data['name'], data['module'], data['tracking']
            args, kwargs = data['args'], data['kwargs']

            index = f"{module}.{name}"
            func = self.funcs[index]
            if func.delaytime > 0:  # Task delay.
                logger.log(f"Task '{uuid}' delayed in {func.delaytime} seconds.")
                time.sleep(func.delaytime)
            logger.log(f"Task '{uuid}' start to run: func={index}, tracking={tracking}, args={args}, kwargs={kwargs}")
            func = self.funcs[index]
            func(*args, **kwargs)
            logger.log(f"Task '{uuid}' complete.")

    def main(self):
        logger = Logger(msg_prefix='AsyncTaskServer.main(): ', trigger_level=ASYNC_TASK_LOG_LEVEL)
        logger.log("Server initializing...")

        # To register asynctask functions.
        self.registerFunctions()
        if not self.funcs:
            return logger.log("No asynctask funcions registered. AsyncTaskServer now quit.", level="FATAL")

        # Start to listen socket.
        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            if os.path.exists(self.sock):
                os.unlink(self.sock)
            server.bind(self.sock)
            server.listen(0)
        except Exception as e:
            return logger.log(f"Failed to initialize server: {str(e)}", level="FATAL")
        logger.log("Server up!")

        # start worker.
        with Pool(processes=2) as pool:
            while True:
                connection, _ = server.accept()
                pool.apply_async(self.worker, (connection, ))

            # quit.
            connection.close()
        # while True:
        #     connection, _ = server.accept()
        #     self.worker(connection)

        # quit.
        # connection.close()
