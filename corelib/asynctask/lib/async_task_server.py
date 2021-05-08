from corelib.tools.logger import Logger
from .defaults import (
    ASYNCTASK_BIND_ADDR,
    ASYNCTASK_BIND_PORT,
    ASYNCTASK_WORKERS,
    ASYNCTASK_REGISTER_MODULE,
    ASYNCTASK_LOG_LEVEL
)

from .async_task_client import HEADER_LENTGH
import json
from django.conf import settings
from importlib import import_module
from tornado import gen, ioloop, tcpserver, iostream
from functools import partial


class AsyncServer(tcpserver.TCPServer):
    def __init__(self, chunk_size=None, logger=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = Logger(trigger_level=ASYNCTASK_LOG_LEVEL) if logger is None else logger
        self.chunk_size = 1024 if chunk_size is None else chunk_size
        self.funcs = {}

    async def handle_stream(self, stream, address):
        self.logger.msg_prefix = 'AsyncServer.handle_stream(): '

        # handle TCP connetion.
        while True:
            try:
                self.logger.log("To receive data from clients...", level='DEBUG')
                data_b = await stream.read_bytes(self.chunk_size, partial=True)
                self.logger.log("To parsing client data header...", level='DEBUG')
                header = data_b[:HEADER_LENTGH]
                data_len = int(header.decode('utf-8').split(':')[1])
                while len(data_b) < data_len:
                    data_b += await stream.read_bytes(self.chunk_size)
                self.logger.log("To parsing client data body...", level='DEBUG')
                data = json.loads(data_b[HEADER_LENTGH:].decode('utf-8'))
                self.logger.log(f"New task received: {str(data)}", level="INFO")
                result = 'OK'
                await stream.write(result.encode('utf-8'))
            except iostream.StreamClosedError:  # Normally stoped connection by client.
                self.logger.log(f"Returned result for client with value: '{result}'", level='DEBUG')
                break
            except Exception as e:
                self.logger.log(str(e), level="ERROR")
                result = 'ERROR'
                break

        # To do the real work.
        if result == 'OK':
            self.logger.log(f"Now to prepare to run the blocking task.", level='DEBUG')
            uuid, name, module = data['uuid'], data['name'], data['module']
            tracking, delaytime = data['tracking'], data['delaytime']
            args, kwargs = data['args'], data['kwargs']

            index = f"{module}.{name}"
            func = self.funcs[index]

            # Delays.
            if isinstance(delaytime, int) and delaytime > 0:
                self.logger.log(f"Task '{uuid}' delayed in {delaytime} seconds.")
                await gen.sleep(func.delaytime)
            elif func.delaytime > 0:  # Task delay.
                self.logger.log(f"Task '{uuid}' delayed in {func.delaytime} seconds.")
                await gen.sleep(func.delaytime)

            # To run the real blocking work in IOLoop.
            self.logger.log(f"Task '{uuid}' start to run: func={index}, tracking={tracking}, args={args}, kwargs={kwargs}")
            func = partial(func, **kwargs)
            await ioloop.IOLoop.current().run_in_executor(None, func, *args)
            self.logger.log(f"Task '{uuid}' complete.")


class MainServer(object):
    def __init__(
        self,
        bind_addr: str = None,
        bind_port: int = None,
        subps: int = None,
        logger: Logger = None
    ) -> None:

        self.bind_addr = ASYNCTASK_BIND_ADDR if bind_addr is None else bind_addr
        self.bind_port = ASYNCTASK_BIND_PORT if bind_port is None else bind_port
        self.subps = ASYNCTASK_WORKERS if subps is None else subps
        self.logger = Logger(trigger_level=ASYNCTASK_LOG_LEVEL) if logger is None else logger
        self.funcs = {}

    def registerFunctions(self):
        self.logger.msg_prefix = 'AsyncServer.registerFunctions(): '

        for app in filter(lambda s: not s.startswith('django.'), settings.INSTALLED_APPS):
            mod_str = f'{app}.{ASYNCTASK_REGISTER_MODULE}'
            try:
                mod = import_module(mod_str)
            except Exception as e:
                self.logger.log(f"Ignore invalid django-installed app: '{app}'.")
                self.logger.log(f"{str(e)}", level='DEBUG')
            else:
                for attr_name in filter(lambda a: not a.startswith('_'), dir(mod)):
                    func = getattr(mod, attr_name)
                    if getattr(func, 'is_asynctask', False):
                        index = f'{mod_str}.{attr_name}'
                        self.funcs[index] = func
                        self.logger.log(f"To register asynctask funcion '{index}' succeeded.")

    def main(self):
        self.logger.msg_prefix = 'AsyncServer.main(): '
        self.logger.log("Server initializing...")

        # To register asynctask functions.
        self.registerFunctions()
        if not self.funcs:
            return self.logger.log("No asynctask funcions registered. AsyncServer now quit.", level="FATAL")

        # To init tornado tcpserver.
        server = AsyncServer()
        server.funcs = self.funcs
        server.listen(self.bind_port, self.bind_addr)
        server.start(self.subps)  # To fork process
        ioloop.IOLoop.current().start()
