# StankinBot Database core module

""" Модуль базы данных
См. https://github.com/egormanga/StankinBot/issues/13
"""

from __future__ import annotations

import os, dill, asyncio
#from contextlib import asynccontextmanager
from . import CoreModule
from ..utils import *

class DatabasedField(XABC):
	class DatabasedProxy(XABC):
		# public:
		field: type
		db: DatabaseModule
		var: str

		# internal:
		_value: ...

		def __repr__(self):
			return f"<Databased proxy for field {self.var}>"

		def __enter__(self):
			self._value = self.get()
			return self._value

		def __exit__(self, exc_type, exc, tb):
			if (exc is None): self.set(self._value)
			del self._value

		def get(self):
			try: value = self.db.get(self.var)
			except KeyError: self.set(value := self.field.__base__())
			return value

		def set(self, value):
			self.db.set(self.var, value)

	# internal:
	_field: ...

	def __init__(self, field):
		self._field = field

	def __repr__(self):
		return f"<Databased field {self._field.__name__}>"

	def __get__(self, obj, cls):
		if (obj is None): return cls.__getattribute__(cls, self._field.__name__)
		db = obj.bot.modules.core.database
		var = (obj.__class__.__qualname__ + '.' + self._field.__name__)
		return self.DatabasedProxy(field=self._field, db=db, var=var)

	def __set__(self, obj, value):
		if (obj is None): return cls.__setattr__(cls, self._field.__name__, value)
		db = obj.bot.modules.core.database
		var = (obj.__class__.__qualname__ + '.' + self._field.__name__)
		return db.set(var, value)

	#@asynccontextmanager
	#async def rlock(self):
	#	try:
	#		r = await self._rlock.acquire()
	#		self._rcnt += 1
	#		if (self._rcnt == 1): await self._wlock.acquire()
	#		self._rlock.release()
	#		yield r
	#	finally:
	#		await self._rlock.acquire()
	#		self._rcnt -= 1
	#		if (self._rcnt == 0): self._wlock.release()
	#		self._rlock.release()
	#
	#@asynccontextmanager
	#async def wlock(self, rlock=None):
	#	try:
	#		if (rlock is None): await self._rlock.acquire()
	#		yield await self._wlock.acquire()
	#	finally: self._wlock.release()

@export
def databased(x): return DatabasedField(x)

@export
class DatabaseModule(CoreModule):
	events = []

	# public:
	path: filename[str]

	# private:
	db: -- dict

	# internal:
	_loaded: -- bool

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.db = dict()
		self._loaded = bool()

	async def init(self):
		self.load()
		self._loaded = True

	async def unload(self):
		if (self._loaded): self.save()

	def load(self):
		if (os.path.exists(self.path)):
			self.db = dill.load(open(self.path, 'rb'))

	def save(self):
		dill.dump(self.db, open(self.path, 'wb'))

	def get(self, var):
		return self.db[var]

	def set(self, var, value):
		self.db[var] = value

# by Sdore, 2021-22
#  stbot.sdore.me
