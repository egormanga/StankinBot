# StankinBot MultiFront frontend module

""" Модуль MultiFront
См. https://github.com/egormanga/StankinBot/issues/1
"""

from __future__ import annotations

from collections import defaultdict
from . import PlatformFrontendModule
from ..utils import *

@export
class MultiFrontModule(PlatformFrontendModule):
	# attributes:
	name = 'multifront'
	events = []

	# private:
	fronts: -- dict

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.fronts = dict()

	def register_front(self, module):
		self.fronts[module.name] = module

	def unregister_front(self, module):
		m = self.fronts.pop(module.name)
		assert (m is module)

	async def send(self, to, *args, **kwargs):
		front = self.fronts[to.front]
		return await front.send(to, *args, **kwargs)

	async def send_mass(self, to, *args, **kwargs):
		tofront = defaultdict(list)
		for i in to:
			tofront[i.front].append(i)

		res = list()
		for front, to in tofront.items():
			front = self.fronts[to.front]
			try: res += await front.send_mass(to, *args, **kwargs)
			except Exception as ex: raise # TODO, issue #16
		return res

# by Sdore, 2021-22
#  stbot.sdore.me
