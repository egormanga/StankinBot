# StankinBot Database core module

""" Модуль базы данных
См. https://github.com/egormanga/StankinBot/issues/13
"""

from __future__ import annotations

import os, time, pickle, shutil, asyncio, datetime, collections
#from contextlib import asynccontextmanager
from . import CoreModule
from ..utils import *

class DatabasedField(XABC):
	@contextmanager
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
			else:
				if (not isinstance(value, self.field.__base__)):
					os.makedirs(backupdir := os.path.join(os.path.dirname(self.db.path), '.backup/'),
					            exist_ok=True)
					shutil.copy(self.db.path,
					            backup := os.path.join(backupdir,
					                                   f"{os.path.basename(self.db.path)}-cast"
					                                   f"-{self.type}:{self.var}"
					                                   f"-{value.__class__.__name__}-to"
					                                   f"-{self.field.__base__.__name__}"
					                                   f"-{time.strftime('%Y.%m.%d-%H:%M:%S')}.bak"))
					self.db.log(f"Warning: type of field {self.type}:{self.var} has changed from"
					            f"{value.__class__.__name__} to {self.field.__base__.__name__}."
					            f" Trying to cast it or fall back to clearing. A backup with name"
					            f" {os.path.basename(backup)} has been created.")
					try:
						await self.set(value := self.field.__base__(value))
					except Exception:
						await self.set(value := await ensure_async(self.default_factory)(self.obj))
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
@decorator
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
		try: self.load()
		finally: self.metadata['version'] = self.version  # bump

	async def unload(self):
		self.save()

	def load(self):
		if (os.path.exists(self.path)):
			with open(self.path, 'rb') as f:
				db = pickle.load(f)

			assert (db['metadata']['version'] == self.version)

			for i in self.db_fields:
				setattr(self, i, db.pop(i, {}))
			assert (not db)

			self._loaded = True

	def save(self):
		backup = None
		if (os.path.exists(self.path) and not self._loaded):
			os.makedirs(backupdir := os.path.join(os.path.dirname(self.path), '.backup/'), exist_ok=True)
			os.rename(self.path, backup := os.path.join(backupdir, f"{os.path.basename(self.path)}-corrupted-"
			                                                       f"{time.strftime('%Y.%m.%d-%H:%M:%S')}.bak"))
			self.log(f"Warning: creating a new database while another is present."
			         f" A backup with name {os.path.basename(backup)} has been created.")

		db = {i: getattr(self, i) for i in self.db_fields}

		try:
			with open(self.path, 'wb') as f:
				pickle.dump(db, f)
		except Exception:
			if (backup is not None): shutil.copy(backup, self.path)
			raise

	async def get(self, type, var, **kwargs):
		return self.get_sync(type, var, **kwargs)

	def get_sync(self, type, var, *, lifetime=None):
		assert (type in self.db_fields)
		data = getattr(self, type)

		if (lifetime is not None):
			try: changed = data[var]['changed']
			except KeyError: pass  # never changed
			else:
				now = datetime.datetime.now().astimezone()
				if (now >= changed + lifetime): raise KeyError(var, f"outdated by {now - (changed + lifetime)}")

		return data[var]['value']

	async def set(self, type, var, value, **kwargs):
		self.set_sync(type, var, value, **kwargs)

	def set_sync(self, type, var, value, *, changed=None):
		if (changed is None): changed = datetime.datetime.now().astimezone()
		assert (type in self.db_fields)

		data = getattr(self, type)

		try: field = data[var]
		except KeyError: field = data[var] = dict()

		field['value'] = value
		field['changed'] = changed

	async def delete(self, type, var, **kwargs):
		self.delete(type, var, **kwargs)

	def delete_sync(self, type, var, *, changed=None):
		if (changed is None): changed = datetime.datetime.now().astimezone()
		assert (type in self.db_fields)

		data = getattr(self, type)

		try: field = data[var]
		except KeyError: return

		del field['value']
		field['changed'] = changed

# by Sdore, 2021-22
#  stbot.sdore.me
