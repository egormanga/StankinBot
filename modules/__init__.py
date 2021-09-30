# StankinBot Module base class

from __future__ import annotations

from abc import *
from .utils import *

@export
class Module(XABC):
	bot: Bot
	events: list = ...

	def __init__(self, bot):
		self.bot = bot

	async def init(self): ...

	async def proc(self): ...

# by Sdore, 2021
# stbot.sdore.me
