# StankinBot Database core module

""" Модуль базы данных
См. https://github.com/egormanga/StankinBot/issues/13
"""

from __future__ import annotations

import os, dill, time, asyncio, datetime, collections
#from contextlib import asynccontextmanager
from . import CoreModule
from ..utils import *

class DatabasedField(XABC):
	class DatabasedProxy(XABC):
		# public:
		db: DatabaseModule
		obj: object
		type: str
		var: str
		field: type
		lifetime: datetime.timedelta
		default_factory: callable

		# internal:
		_value: ...

		def __repr__(self):
			return f"<Databased proxy for field {self.type}:{self.var} of {self.obj}>"

		async def __aenter__(self):
			self._value = await self.get()
			return self._value

		async def __aexit__(self, exc_type, exc, tb):
			if (exc is None): await self.set(self._value)
			del self._value

		async def get(self):
			try: value = await self.db.get(self.type, self.var, lifetime=self.lifetime)
			except KeyError: await self.set(value := await ensure_async(self.default_factory)(self.obj))
			return value

		async def set(self, value):
			await self.db.set(self.type, self.var, value)

		async def delete(self):
			await self.db.delete(self.type, self.var)

	# internal:
	_type: ...
	_field: ...
	_lifetime: ...
	_default_factory: ...

	def __init__(self, type, field):
		self._type, self._field = type, field
		self._lifetime = None
		self._default_factory = lambda obj: field.__base__()

	def __repr__(self):
		return f"<Databased field {self._type}:{self._field.__name__}>"

	def __get__(self, obj, cls):
		if (obj is None): return cls.__getattribute__(cls, self._field.__name__)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return self.DatabasedProxy(
			db = db,
			obj = obj,
			type = self._type,
			var = var,
			field = self._field,
			lifetime = self._lifetime,
			default_factory = self._default_factory,
		)

	def __set__(self, obj, value):
		if (obj is None): return cls.__setattr__(cls, self._field.__name__, value)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return db.set_sync(self._type, var, value)

	def __delete__(self, obj):
		if (obj is None): return cls.__delattr__(cls, self._field.__name__)
		db = obj.bot.modules.core.database
		var = f"{obj.__class__.__qualname__}.{self._field.__name__}"
		return db.delete_sync(self._type, var)

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
def databased(type): return lambda x: DatabasedField(type, x)

@export
class DatabaseModule(CoreModule):
	version = 2
	db_fields = (
		'state',
		'user',
		'group',
		'common',
		'cache',
		'metadata',
	)
	events = []

	# public:
	path: filename[str]

	# private:
	state: -- dict
	user: -- dict
	group: -- dict
	common: -- dict
	cache: -- dict
	metadata: -- dict

	# internal:
	_loaded: -- bool

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.state = dict()
		self.user = dict()
		self.group = dict()
		self.common = dict()
		self.cache = dict()
		self.metadata = dict()
		self._loaded = bool()

	async def init(self):
		self.load()

	async def unload(self):
		self.save()

	def load(self):
		if (os.path.exists(self.path)):
			with open(self.path, 'rb') as f:
				db = dill.load(f)

			assert (db['metadata']['version'] == self.version)

			for i in self.db_fields:
				setattr(self, i, db.pop(i, {}))
			assert (not db)

			self._loaded = True
		else:
			self.metadata['version'] = self.version

	def save(self):
		if (os.path.exists(self.path) and not self._loaded):
			os.rename(self.path, backup := f"{self.path}.{time.strftime('%Y.%m.%d-%H:%M:%S')}.bak")
			self.log(f"Warning: creating a new database while another is present. A backup with name {os.path.basename(backup)} has been created.")

		db = {i: getattr(self, i) for i in self.db_fields}

		with open(self.path, 'wb') as f:
			dill.dump(db, f)

	async def get(self, type, var, **kwargs):
		return self.get_sync(type, var, **kwargs)

	def get_sync(self, type, var, *, lifetime=None):
		assert (type in self.db_fields)
		data = getattr(self, type)

		if (lifetime is not None):
			try: changed = data[var]['changed']
			except KeyError: pass  # never changed
			else:
				now = datetime.datetime.now(tz=datetime.timezone.utc)
				if (now >= changed + lifetime): raise KeyError(var, f"is outdated by {now - (changed + lifetime)}")

		return data[var]['value']

	async def set(self, type, var, value, **kwargs):
		self.set_sync(type, var, value, **kwargs)

	def set_sync(self, type, var, value, *, changed=None):
		if (changed is None): changed = datetime.datetime.now(tz=datetime.timezone.utc)
		assert (type in self.db_fields)

		data = getattr(self, type)

		try: field = data[var]
		except KeyError: field = data[var] = dict()

		field['value'] = value
		field['changed'] = changed

	async def delete(self, type, var, **kwargs):
		self.delete(type, var, **kwargs)

	def delete_sync(self, type, var, *, changed=None):
		if (changed is None): changed = datetime.datetime.now(tz=datetime.timezone.utc)
		assert (type in self.db_fields)

		data = getattr(self, type)

		try: field = data[var]
		except KeyError: return

		del field['value']
		field['changed'] = changed

# by Sdore, 2021-22
#  stbot.sdore.me
