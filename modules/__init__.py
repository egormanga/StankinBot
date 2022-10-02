# StankinBot Module base class

from __future__ import annotations

from abc import *
from .utils import *

@export
class Module(XABC):
	# attributes:
	type: str = ...
	name: str = ...
	events: list = ...
	log_color = 39

	# public:
	bot: Bot

	# internal:
	_inited: bool
	_started: bool

	def __init__(self, bot, **kwargs):
		""" Прочитать конфигурацию и инициализировать поля. Не создавать зависимостей от состояния. """

		super().__init__(**kwargs)
		self.bot = bot
		self._started = self._inited = bool()

	def __del__(self):
		try:
			if (self._started): self.log("Destructing but still running.")
			if (self._inited): self.log("Destructing but still loaded.")
		except AttributeError: pass

	def __repr__(self):
		return f"<Module {self}>"

	def __str__(self):
		return self.__class__.__module__.partition('modules.')[2]

	def __delattr__(self, x):
		try: super().__delattr__(x)
		except AttributeError as ex: self.log(f"\033[1;93mWarning:\033[22m", f"trying to delete missing attribute «{ex.args[0]}»", format_exc(ex)); traceback.print_exc(); print()

	async def init(self):
		""" Загрузить состояние, готовое к использованию. Можно создавать зависимости (открывать файлы, т.д.). Не запускать службы, не создавать нагрузку. """

		self._inited = True

	async def start(self):
		""" Запустить службы. Можно создавать нагрузку. """

		self._started = True

	async def stop(self):
		""" Остановить службы. Прекратить всю нагрузку. """

		self._started = False

	async def unload(self):
		""" Сохранить все данные, закрыть все зависимости, удалить состояние, освободить память. """

		self._inited = False

	def log(self, *args, sep=' '):
		self.bot.log(f"\033[{self.log_color}m[\033[3m{self}\033[23m]\033[39m", sep.join(map(str, args)))

	@classproperty
	def type(cls) -> str:
		return cls.__module__.partition('modules.')[2].partition('.')[0]

	@classproperty
	def name(cls) -> str:
		return cls.__module__.partition('modules.')[2].partition('.')[2]

# by Sdore, 2021-22
#  stbot.sdore.me
