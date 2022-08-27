#!/usr/bin/env python3
# StankinBot

from __future__ import annotations

import sys, yaml, os.path, asyncio, operator, importlib, traceback
from collections import defaultdict
from .modules import Module
from .modules.utils import *

class Bot(XABC):
	config: dict
	modules: -- dict[dict]

	def __init__(self, config):
		super().__init__(config=config)
		self.modules = DefaultDictAttrProxy(DictAttrProxy)

		for k, v in self.config.items():
			for i in v:
				m = importlib.import_module(f'.modules.{k}.{i}', package=__package__)
				moduleclass = first(v for k in m.__all__ if isinstance(v := getattr(m, k), type) and issubclass(v, Module))
				self.register_module(moduleclass)

	async def run(self):
		await self.init_modules()
		await self.start_modules()

		print("\033[1mStarted.\033[0m")

		try:
			await asyncio.sleep(float('inf')) # TODO
		finally:
			print("\r\033[K\033[2mShutting down...\033[0m", end='', flush=True, file=sys.stderr)
			await self.stop_modules()
			await self.unload_modules()
			print("\r\033[K\033[1mExit.\033[0m", end='', flush=True, file=sys.stderr)

	def register_module(self, moduleclass):
		path = moduleclass.__module__.partition('modules.')[2]
		conf = operator.attrgetter(path)(self.config)
		m = moduleclass(self, **conf or {})
		self.modules[moduleclass.type][moduleclass.name] = m

	@staticmethod
	def _format_exc(ex):
		return str().join(traceback.format_exception_only(type(ex), ex)).strip()

	async def init_modules(self):
		for i in self.modules.values():
			for m in i.values():
				try: await m.init()
				except Exception as ex: print(f"Failed to init module {m}: {self._format_exc(ex)}"); traceback.print_exc()

	async def start_modules(self):
		for i in self.modules.values():
			for m in i.values():
				try: await m.start()
				except Exception as ex: print(f"Failed to start module {m}: {self._format_exc(ex)}"); traceback.print_exc()

	async def stop_modules(self):
		for i in self.modules.values():
			for m in i.values():
				try: await m.stop()
				except Exception as ex: print(f"Failed to stop module {m}: {self._format_exc(ex)}"); traceback.print_exc()

	async def unload_modules(self):
		for i in self.modules.values():
			for m in i.values():
				try: await m.unload()
				except Exception as ex: print(f"Failed to unload module {m}: {self._format_exc(ex)}"); traceback.print_exc()

def main():
	config = DictAttrProxy(yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yml'))))
	bot = Bot(config)

	try: asyncio.run(bot.run())
	except KeyboardInterrupt as ex: exit(ex)

if (__name__ == '__main__'): exit(main())

# by Sdore, 2021-22
#  stbot.sdore.me
