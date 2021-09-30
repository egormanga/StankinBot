# StankinBot utility module

import inspect
from abc import ABCMeta, abstractmethod, abstractproperty
from types import FunctionType

__all__ = ('abstractmethod', 'abstractproperty')

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

class XABCMeta(ABCMeta):
	def __new__(metacls, name, bases, classdict):
		annotations = classdict.get('__annotations__', {})
		classdict['__slots__'] = tuple(i for i in annotations if classdict.get(i) is not ...)
		classdict.update({i: abstractproperty() for i in annotations if classdict.get(i) is ...})
		classdict.update({k: abstractmethod(v) for v in classdict.items()  # `def f(): ...`
		                                       if isinstance(v, FunctionType) and v.__code__.co_code == b'd\x00S\x00' and v.__code__.co_consts == (None,)})

		if ('__init__' not in classdict):
			def __init__(self, *args, **kwargs):
				for i in self.__slots__:
					setattr(self, i, kwargs.pop(i))

				if (bases): super(bases[0], self).__init__(*args) # TODO: kwargs

				if (kwargs): raise TypeError(f"{name}.__init__() got extra argument{'s'*(len(kwargs) > 1)}: {', '.join(kwargs)}")
			classdict['__init__'] = __init__

		return super().__new__(metacls, name, bases, classdict)

@export
class XABC(metaclass=XABCMeta): pass

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
