#!/usr/bin/env python3
# StankinBot main

import os, yaml, signal, asyncio, traceback, watchfiles
from .modules.utils import format_exc, recursive_reload, DictAttrProxy

async def main():
	srcdir = os.path.dirname(__file__)

	loop = asyncio.get_event_loop()
	stop = asyncio.Event()
	loop.add_signal_handler(signal.SIGINT, lambda: stop.set())
	loop.add_signal_handler(signal.SIGTERM, lambda: stop.set())

	try:
		while (True):
			config = DictAttrProxy(yaml.safe_load(open(os.path.join(srcdir, 'config.yml'))))
			from . import StankinBot as stankin_bot

			async with stankin_bot.Bot(config) as bot:
				#try:
				#	async for changes in watchfiles.awatch(srcdir):
				#		print("Source has changed, reloading.")
				#		break
				#except RuntimeError: pass
				await stop.wait(); break

			#try: recursive_reload(stankin_bot)
			#except (SyntaxError, ImportError) as ex: print(f"Failed to reload the source:", format_exc(ex)); traceback.print_exc()
	except KeyboardInterrupt as ex: exit(ex)

if (__name__ == '__main__'): exit(asyncio.run(main()))

# by Sdore, 2022
# stbot.sdore.me
