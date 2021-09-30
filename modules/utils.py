# StankinBot utility module

import abc, inspect
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

class XABCMeta(abc.ABCMeta):
	def __new__(metacls, name, bases, classdict):
		annotations = classdict.get('__annotations__', {})
		classdict['__slots__'] = tuple(i for i in annotations if classdict.get(i) is not ...)
		classdict.update({i: abc.abstractproperty() for i in annotations if classdict.get(i) is ...})
		classdict.update({k: abc.abstractmethod(v) for v in classdict.items()  # `def f(): ...`
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

@decorator
class classproperty:
	def __init__(self, f):
		self.f = f

	def __get__(self, obj, cls):
		return self.f(cls)

# by Sdore, 2021
# stbot.sdore.me
