#!/usr/bin/env python3
# StankinBot main

import os, yaml, asyncio, traceback, watchfiles
from .modules.utils import format_exc, recursive_reload, DictAttrProxy

def _handle_task_result(task: asyncio.Task):
	try: task.result()
	except asyncio.CancelledError: pass
	except Exception as ex: print(f"Error in task {task}: {format_exc(ex)}"); traceback.print_exc()

async def main():
	srcdir = os.path.dirname(__file__)

	try:
		while (True):
			config = DictAttrProxy(yaml.safe_load(open(os.path.join(srcdir, 'config.yml'))))

			from . import StankinBot as stankin_bot
			bot = stankin_bot.Bot(config)
			task = asyncio.create_task(bot.run())
			task.add_done_callback(_handle_task_result)

			async for changes in watchfiles.awatch(srcdir):
				task.cancel("Source has changed, reloading.")
				break

			try: await task
			except asyncio.CancelledError: pass

			try: recursive_reload(stankin_bot)
			except (SyntaxError, ImportError) as ex: print(f"Failed to reload the source: {format_exc(ex)}"); traceback.print_exc()
	except KeyboardInterrupt as ex: exit(ex)

if (__name__ == '__main__'): exit(asyncio.run(main()))

# by Sdore, 2022
# stbot.sdore.me
