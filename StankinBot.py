#!/usr/bin/env python3
# StankinBot

from __future__ import annotations

import sys, asyncio, operator, importlib, traceback
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
		print("\r\033[K\033[2mInitializing…\033[0m", end='', flush=True, file=sys.stderr)
		await self.init_modules()
		print("\r\033[K\033[2mStarting…\033[0m", end='', flush=True, file=sys.stderr)
		await self.start_modules()

		print("\r\033[K\033[1mStarted.\033[0m", flush=True, file=sys.stderr)

		try: await asyncio.sleep(float('inf'))
		except asyncio.CancelledError as ex:
			if (ex.args): print(f"\r\033[K\033[3m{ex.args[0]}\033[0m", file=sys.stderr)
		finally:
			print("\r\033[K\033[2mStopping…\033[0m", end='', flush=True, file=sys.stderr)
			await self.stop_modules()
			print("\r\033[K\033[2mShutting down…\033[0m", end='', flush=True, file=sys.stderr)
			await self.unload_modules()
			print("\r\033[K\033[1mExit.\033[0m", flush=True, file=sys.stderr)

	def register_module(self, moduleclass):
		path = moduleclass.__module__.partition('modules.')[2]
		conf = operator.attrgetter(path)(self.config)
		m = moduleclass(self, **conf or {})
		self.modules[moduleclass.type][moduleclass.name] = m

	async def init_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mInitializing…  [\033[3m{m}\033[23m]\033[22m", end='', flush=True, file=sys.stderr)
				try: await m.init()
				except Exception as ex: print(f"Failed to init module {m}: {format_exc(ex)}"); traceback.print_exc()

	async def start_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mStarting…  [\033[3m{m}\033[23m]\033[22m", end='', flush=True, file=sys.stderr)
				try: await m.start()
				except Exception as ex: print(f"Failed to start module {m}: {format_exc(ex)}"); traceback.print_exc()

	async def stop_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mStopping…  [\033[3m{m}\033[23m]\033[22m", end='', flush=True, file=sys.stderr)
				try: await m.stop()
				except Exception as ex: print(f"Failed to stop module {m}: {format_exc(ex)}"); traceback.print_exc()

	async def unload_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mUnloading…  [\033[3m{m}\033[23m]\033[22m", end='', flush=True, file=sys.stderr)
				try: await m.unload()
				except Exception as ex: print(f"Failed to unload module {m}: {format_exc(ex)}"); traceback.print_exc()

# by Sdore, 2021-22
#  stbot.sdore.me
