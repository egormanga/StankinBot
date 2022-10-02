# StankinBot utility module

import time, locale, asyncio, inspect, functools, importlib, traceback, collections
from abc import ABCMeta, abstractmethod, abstractproperty
from types import ModuleType, FunctionType

# These are just for documenting/readability purposes via '@', instead of comments:
def decorator(x): return x
def contextmanager(x): return x

@decorator
def export(x):
	""" Декоратор, экспортирующий функцию или класс для использования с `from _ import *`, добавляя его имя в __all__. """

	globals = inspect.stack()[1][0].f_globals
	if ('__all__' not in globals): all = globals['__all__'] = list()
	elif (not isinstance(globals['__all__'], list)): all = globals['__all__'] = list(globals['__all__'])
	else: all = globals['__all__']
	all.append(x.__name__.rpartition('.')[-1])
	return x
export(export)  # itself
export(decorator)
export(contextmanager)

export(abstractmethod)
export(abstractproperty)

@export
def first(it): return next(iter(it))
@export
def only(it):
        it = iter(it)
        try: return next(it)
        finally:
                try: next(it)
                except StopIteration: pass
                else: raise StopIteration("Only a single value expected")

@export
def assert_(x): assert (x); return True

@export
def format_exc(ex): return str().join(traceback.format_exception_only(type(ex), ex)).strip()

@export
@decorator
class classproperty:
	__slots__ = ('__func__',)

	def __init__(self, f):
		self.__func__ = f

	def __get__(self, obj, cls):
		return self.__func__(cls)

def get_property_annotations(p):
	if (isinstance(p, property)): p = p.fget
	elif (isinstance(p, classproperty)): p = p.__func__
	elif (isinstance(p, functools.cached_property)): p = p.func
	return p.__annotations__

@export
def recursive_reload(module):
	""" Рекурсивно перезагрузить модуль `module'. """

	importlib.reload(module)
	return # XXX FIXME

	for i in vars(module).values():
		if (isinstance(i, ModuleType)):
			recursive_reload(i)

@export
@decorator
def ensure_async(f):
	@functools.wraps(f)
	async def decorated(*args, **kwargs):
		r = f(*args, **kwargs)
		return (await r if (asyncio.iscoroutinefunction(f)) else r)
	return decorated

@export
@contextmanager
class timecounter:
	__slots__ = ('start', 'end')

	def __init__(self):
		self.start = self.end = None

	def __enter__(self):
		self.start = time.perf_counter()
		return self

	def __exit__(self, exc_type, exc, tb):
		self.end = time.perf_counter()

	@property
	def time(self):
		if (self.start is None): return None
		elif (self.end is None): return (time.perf_counter() - self.start)
		else: return (self.end - self.start)

class XABCMeta(ABCMeta):
	def __new__(metacls, name, bases, classdict):
		annotations = classdict.get('__annotations__', {})

		classdict['__slots__'] = tuple(k for k, v in annotations.items() if (p := classdict.get(k)) is not ... and not (isinstance(p, (property, classproperty, functools.cached_property)) and (ra := get_property_annotations(p).get('return')) and ra == v.removeprefix('--').strip()))

		if (conflicts := {i: c for i in classdict['__slots__'] if (c := metacls.conflicts(i, bases)) is not None}):
			raise ValueError(f"There are conflicts between members of {name} and its bases: {', '.join(f'{i} in {c}' for i, c in conflicts.items())}")

		classdict.update({i: abstractproperty() for i in annotations if classdict.get(i) is ...})  # `x: ...`
		classdict.update({k: abstractmethod(v) for v in classdict.items() if isinstance(v, FunctionType) and v.__code__.co_code == b'd\0S\0' and v.__code__.co_consts == (None,)})  # `def f(): ...`

		return super().__new__(metacls, name, bases, classdict)

	@classmethod
	def conflicts(cls, name, bases):
		for c in bases:
			if (name in getattr(c, '__slots__', ())): return c.__name__
			if ((r := cls.conflicts(name, c.__bases__)) is not None): return r

@export
class XABC(metaclass=XABCMeta): # TODO: verify property types
	def __init__(self, **kwargs):
		for i in self.__slots__:
			a = str(self.__annotations__.get(i))
			if (not a.startswith('...') and not a.startswith('--')):
				setattr(self, i, kwargs.pop(i))

		if (kwargs): raise TypeError(f"{self.__class__.__name__}.__init__() got extra argument{'s'*(len(kwargs) > 1)}: {', '.join(kwargs)}")

@export
class DictAttrProxy(collections.UserDict):
	""" Прокси для доступа к ключам по атрибутам. """

	def __init__(self, dict=None, /, **kwargs):
		super().__setattr__('data', {})
		if (dict is not None): self.update(dict)
		if (kwargs): self.update(kwargs)

	def __getitem__(self, x):
		DictAttrProxy = self.__class__
		r = super().__getitem__(x)
		if (isinstance(r, dict) and not isinstance(r, DictAttrProxy)): return DictAttrProxy(r)
		else: return r

	def __getattr__(self, x):
		d = self.__getattribute__('data')
		try: return getattr(d, x)
		except AttributeError as ex:
			try: return self[x]
			except KeyError as ex: e = ex
		e.__suppress_context__ = True
		raise AttributeError(*e.args) from e.with_traceback(None)

	def __setattr__(self, k, v):
		self.__setitem__(k, v)

	def __delattr__(self, x):
		self.__delitem__(x)

@export
class DefaultDictAttrProxy(DictAttrProxy):
	def __init__(self, default, /, *args, **kwargs):
		super().__init__(*args, **kwargs)
		super(collections.UserDict, self).__setattr__('default_factory', default)

	def __getitem__(self, x):
		try: return super().__getitem__(x)
		except KeyError: return self.__missing__()

	def __missing__(self, x):
		if (self.default_factory is None): raise KeyError(x)
		r = self[x] = self.default_factory()
		return r

@export
@contextmanager
class lc:
	__slots__ = ('category', 'lc', 'pl')

	def __init__(self, lc: str, category: int = locale.LC_ALL):
		self.lc, self.category = lc, category

	def __enter__(self):
		self.pl = locale.setlocale(self.category)
		locale.setlocale(self.category, self.lc)

	def __exit__(self, type, value, tb):
		locale.setlocale(self.category, self.pl)

# by Sdore, 2021-22
#  stbot.sdore.me
