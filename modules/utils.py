# StankinBot utility module

import locale, inspect
from abc import ABCMeta, abstractmethod, abstractproperty
from types import FunctionType

def decorator(f): return f  # just for documenting/readability purposes via '@', instead of comments

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

export(abstractmethod)
export(abstractproperty)

@export
def first(x): return next(iter(x))

@export
def assert_(x): assert (x); return True

class XABCMeta(ABCMeta):
	def __new__(metacls, name, bases, classdict):
		annotations = classdict.get('__annotations__', {})
		classdict['__slots__'] = tuple(k for k, v in annotations.items() if classdict.get(k) is not ...)
		if (conflicts := {i: c for i in classdict['__slots__'] if (c := metacls.conflicts(i, bases)) is not None}):
			raise ValueError(f"There are conflicts between members of {name} and its bases: {', '.join(f'{i} in {c}' for i, c in conflicts.items())}")
		classdict.update({i: abstractproperty() for i in annotations if classdict.get(i) is ...})
		classdict.update({k: abstractmethod(v) for v in classdict.items()  # `def f(): ...`
		                                       if isinstance(v, FunctionType) and v.__code__.co_code == b'd\x00S\x00' and v.__code__.co_consts == (None,)})
		return super().__new__(metacls, name, bases, classdict)

	@classmethod
	def conflicts(cls, name, bases):
		for c in bases:
			if (name in getattr(c, '__slots__', ())): return c.__name__
			if ((r := cls.conflicts(name, c.__bases__)) is not None): return r

@export
class XABC(metaclass=XABCMeta):
	def __init__(self, **kwargs):
		for i in self.__slots__:
			if (self.__annotations__.get(i) not in (..., '...')):
				setattr(self, i, kwargs.pop(i))

		if (kwargs): raise TypeError(f"{self.__class__.__name__}.__init__() got extra argument{'s'*(len(kwargs) > 1)}: {', '.join(kwargs)}")

@export
@decorator
class classproperty:
	def __init__(self, f):
		self.f = f

	def __get__(self, obj, cls):
		return self.f(cls)

@export
class lc:
	__slots__ = ('category', 'lc', 'pl')

	def __init__(self, lc: str, category: int = locale.LC_ALL):
		self.lc, self.category = lc, category

	def __enter__(self):
		self.pl = locale.setlocale(self.category)
		locale.setlocale(self.category, self.lc)

	def __exit__(self, type, value, tb):
		locale.setlocale(self.category, self.pl)

# by Sdore, 2021
# stbot.sdore.me
