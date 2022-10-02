# StankinBot Database core module

""" Модуль базы данных
См. https://github.com/egormanga/StankinBot/issues/13
"""

from __future__ import annotations

import os, dill, asyncio, datetime, collections
#from contextlib import asynccontextmanager
from . import CoreModule
from ..utils import *

class DatabasedField(XABC):
	class DatabasedProxy(XABC):
		# public:
		db: DatabaseModule
		obj: object
		var: str
		field: type
		lifetime: datetime.timedelta
		default_factory: callable

		# internal:
		_value: ...

		def __repr__(self):
			return f"<Databased proxy for field {self.var} of {self.obj}>"

		async def __aenter__(self):
			self._value = await self.get()
			return self._value

		async def __aexit__(self, exc_type, exc, tb):
			if (exc is None): await self.set(self._value)
			del self._value

		async def get(self):
			try: value = await self.db.get(self.var, lifetime=self.lifetime)
			except KeyError: await self.set(value := await ensure_async(self.default_factory)(self.obj))
			return value

		async def set(self, value):
			await self.db.set(self.var, value)

	# internal:
	_field: ...
	_lifetime: ...
	_default_factory: ...

	def __init__(self, field):
		self._field = field
		self._lifetime = None
		self._default_factory = lambda obj: field.__base__()

	def __repr__(self):
		return f"<Databased field {self._field.__name__}>"

	def __get__(self, obj, cls):
		if (obj is None): return cls.__getattribute__(cls, self._field.__name__)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return self.DatabasedProxy(
			db = db,
			obj = obj,
			var = var,
			field = self._field,
			lifetime = self._lifetime,
			default_factory = self._default_factory,
		)

	def __set__(self, obj, value):
		if (obj is None): return cls.__setattr__(cls, self._field.__name__, value)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return db.set_sync(var, value)

	def __delete__(self, obj):
		if (obj is None): return cls.__delattr__(cls, self._field.__name__)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return db.delete_sync(var)

	def cached_getter(self, **kwargs):
		def decorator(f):
			self._lifetime = datetime.timedelta(**kwargs)
			self._default_factory = f
			return f
		return decorator

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
		self.db = collections.defaultdict(dict)
		self._loaded = bool()

	async def init(self):
		self.load()
		self._loaded = True

	async def unload(self):
		if (self._loaded): self.save()

	def load(self):
		if (os.path.exists(self.path)):
			with open(self.path, 'rb') as f:
				db = dill.load(f)
			self.db.update(db)
			assert (self.db['metadata']['version'] == 1)
		else:
			self.db['metadata']['version'] = 1

	def save(self):
		db = dict(self.db)
		with open(self.path, 'wb') as f:
			dill.dump(db, f)

	async def get(self, var, **kwargs):
		return self.get_sync(var, **kwargs)

	def get_sync(self, var, *, lifetime=None):
		if (lifetime is not None):
			try: changed = self.db['changed'][var]
			except KeyError: pass  # never changed
			else:
				now = datetime.datetime.now(tz=datetime.timezone.utc)
				if (now >= changed + lifetime): raise KeyError(var, f"is outdated by {now - (changed + lifetime)}")
		return self.db['data'][var]

	async def set(self, var, value, **kwargs):
		self.set_sync(var, value, **kwargs)

	def set_sync(self, var, value, *, changed=None):
		if (changed is None): changed = datetime.datetime.now(tz=datetime.timezone.utc)
		self.db['data'][var] = value
		self.db['changed'][var] = changed

	async def delete(self, var, **kwargs):
		self.delete(var, **kwargs)

	def delete_sync(self, var, *, changed=None):
		if (changed is None): changed = datetime.datetime.now(tz=datetime.timezone.utc)
		del self.db['data'][var]
		self.db['changed'][var] = changed

# by Sdore, 2021-22
#  stbot.sdore.me
