#!/usr/bin/env python3
# StankinBot main

import os, yaml, asyncio, traceback, watchfiles
from .modules.utils import recursive_reload, DictAttrProxy

async def main():
	srcdir = os.path.dirname(__file__)

	try:
		while (True):
			config = DictAttrProxy(yaml.safe_load(open(os.path.join(srcdir, 'config.yml'))))

			from . import StankinBot as stankin_bot
			bot = stankin_bot.Bot(config)
			task = asyncio.create_task(bot.run())

			async for changes in watchfiles.awatch(srcdir):
				task.cancel("Source has changed, reloading.")
				break

			await task

			try: recursive_reload(stankin_bot)
			except SyntaxError: traceback.print_exc(); pass
	except KeyboardInterrupt as ex: exit(ex)

if (__name__ == '__main__'): exit(asyncio.run(main()))

# by Sdore, 2022
# stbot.sdore.me
