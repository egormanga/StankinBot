# StankinBot Module base class

from __future__ import annotations

from abc import *
from .utils import *

@export
class Module(XABC):
	# public:
	bot: Bot
	events: list = ...

	# properties:
	type: str
	name: str

	def __init__(self, bot, **kwargs):
		""" Прочитать конфигурацию и инициализировать поля. Не создавать зависимостей от состояния. """

		super().__init__(**kwargs)
		self.bot = bot

	def __repr__(self):
		return f"<Module {self}>"

	def __str__(self):
		return self.__class__.__module__.partition('modules.')[2]

	async def init(self): """ Загрузить состояние, готовое к использованию. Можно создавать зависимости (открывать файлы, т.д.). Не запускать службы, не создавать нагрузку. """

	async def start(self): """ Запустить службы. Можно создавать нагрузку. """

	async def stop(self): """ Остановить службы. Прекратить всю нагрузку. """

	async def unload(self): """ Сохранить все данные, закрыть все зависимости, удалить состояние, освободить память. """

	@classproperty
	def type(cls) -> str:
		return cls.__module__.partition('modules.')[2].partition('.')[0]

	@classproperty
	def name(cls) -> str:
		return cls.__module__.partition('modules.')[2].partition('.')[2]

# by Sdore, 2021-22
#  stbot.sdore.me
