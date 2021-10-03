# StankinBot Module base class

from __future__ import annotations

from abc import *
from .utils import *

@export
class Module(XABC):
	bot: Bot
	events: list = ...

	def __init__(self, bot, conf, **kwargs):
		super().__init__(**kwargs)
		self.bot = bot

	def __repr__(self):
		return f"<Module {self}>"

	def __str__(self):
		return self.__class__.__module__.partition('modules.')[2]

	async def init(self): ...

	async def start(self): ...

	async def stop(self): ...

	@classproperty
	def type(cls):
		return cls.__module__.partition('modules.')[2].partition('.')[0]

# by Sdore, 2021
# stbot.sdore.me
