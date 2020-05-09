import asyncio


class CoroutineRunner(object):
    def __init__(self, works):
        """
        works: 二维列表，每个子列表代表一个需要并发执行的任务；子列表第一个元素是执行的函数，其余元素是传给函数的参数;
        """
        self.tasks = []
        self.works = works

    async def concurrent(self):
        loop = asyncio.get_event_loop()
        for real_work in self.works:
            # print(f"===> {str(real_work)}")
            _func, *_params = real_work
            result = asyncio.gather(loop.run_in_executor(None, _func, *_params))
            self.tasks.append(result)
        await asyncio.gather(*self.tasks)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.concurrent())
