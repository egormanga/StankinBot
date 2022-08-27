# StankinBot MultiFront frontend module

from collections import defaultdict
from . import FrontendModule

class MultiFrontModule(FrontendModule):
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

	def command(self, f):
		for front in self.fronts.values():
			front.command(f)
		return f

	def command_unknown(self, f):
		for front in self.fronts.values():
			front.command_unknown(f)
		return f

	def message(self, f):
		for front in self.fronts.values():
			front.message(f)
		return f

	@property
	def fronts(self):
		return self.bot.modules.frontend

# by Sdore, 2021-22
#  stbot.sdore.me
