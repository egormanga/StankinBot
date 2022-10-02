#!/usr/bin/env python3
# StankinBot

from __future__ import annotations

import sys, time, asyncio, operator, importlib, traceback
from .modules import Module
from .modules.utils import *

class Bot(XABC):
	config: dict
	modules: -- dict[dict]

	# internal:
	_logfile: ...

	def __init__(self, config):
		super().__init__(config=config)
		self.modules = DefaultDictAttrProxy(DictAttrProxy)

		self._logfile = open('StankinBot.log', 'a')

		for k, v in self.config.items():
			if (v is None): continue
			for i in v:
				m = importlib.import_module(f'.modules.{k}.{i}', package=__package__)
				moduleclass = first(v for k in m.__all__ if isinstance(v := getattr(m, k), type) and issubclass(v, Module))
				self.register_module(moduleclass)

	async def __aenter__(self):
		with timecounter() as tc:
			print("\r\033[K\033[2mInitializing…\033[22m", end='', file=sys.stderr, flush=True)
			await self.init_modules()
			init_time = tc.time
			print("\r\033[K\033[2mStarting…\033[22m", end='', file=sys.stderr, flush=True)
			await self.start_modules()
			start_time = tc.time
		self.log(f"\033[1mStarted\033[22m in ({round(init_time, 1)} init + {round((start_time - init_time), 1)} start = {round(start_time, 1)}) sec.")
		return self

	async def __aexit__(self, exc_type, exc, tb):
		if (exc is not None and exc.args): self.log(f"\033[3m{exc.args[0]}\033[0m\n")
		print("\r\033[K\033[2mStopping…\033[22m", end='', file=sys.stderr, flush=True)
		await self.stop_modules()
		print("\r\033[K\033[2mShutting down…\033[22m", end='', file=sys.stderr, flush=True)
		await self.unload_modules()
		self.log("\033[1mExit.\033[0m")

	def log(self, *args, sep=' '):
		s = f"\033[1;96m[{time.strftime('%x %X')}]\033[22;39m {sep.join(map(str, args))}\033[0m"
		print('\r\033[K', s, sep='', file=sys.stderr, flush=True)
		print(s, file=self._logfile, flush=True)

	def register_module(self, moduleclass):
		path = moduleclass.__module__.partition('modules.')[2]
		conf = operator.attrgetter(path)(self.config)
		m = moduleclass(self, **conf or {})
		self.modules[moduleclass.type][moduleclass.name] = m

	async def init_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mInitializing…  [\033[3m{m}\033[23m]\033[22m", end='', file=sys.stderr, flush=True)
				try: await m.init()
				except Exception as ex: self.log(f"\033[1mFailed to init module {m}:\033[22m", format_exc(ex)); traceback.print_exc(); print()

	async def start_modules(self):
		for i in self.modules.values():
			for m in i.values():
				print(f"\r\033[K\033[2mStarting…  [\033[3m{m}\033[23m]\033[22m", end='', file=sys.stderr, flush=True)
				try: await m.start()
				except Exception as ex: self.log(f"\033[1mFailed to start module {m}:\033[22m", format_exc(ex)); traceback.print_exc(); print()

	async def stop_modules(self):
		for i in reversed(tuple(self.modules.values())):
			for m in reversed(tuple(i.values())):
				print(f"\r\033[K\033[2mStopping…  [\033[3m{m}\033[23m]\033[22m", end='', file=sys.stderr, flush=True)
				try: await m.stop()
				except Exception as ex: self.log(f"\033[1mFailed to stop module {m}:\033[22m", format_exc(ex)); traceback.print_exc(); print()

	async def unload_modules(self):
		for i in reversed(tuple(self.modules.values())):
			for m in reversed(tuple(i.values())):
				print(f"\r\033[K\033[2mUnloading…  [\033[3m{m}\033[23m]\033[22m", end='', file=sys.stderr, flush=True)
				try: await m.unload()
				except Exception as ex: self.log(f"\033[1mFailed to unload module {m}:\033[22m", format_exc(ex)); traceback.print_exc(); print()

# by Sdore, 2021-22
#  stbot.sdore.me
