# StankinBot Cron core module

""" Модуль запланированных задач
См. https://github.com/egormanga/StankinBot/issues/14
"""

from __future__ import annotations

import time, bisect, asyncio
from . import CoreModule
from .database import databased
from ..utils import *

class Job(XABC):
	at: time[float]
	call: function

	def __le__(self, other):
		return (self.at < other.at)

@export
class CronModule(CoreModule):
	events = []

	# persistent:
	@databased
	class jobs(list): jobs: sorted[[Job]]

	# private:
	is_running: -- bool
	job_added: -- asyncio.Event

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.is_running = bool()
		self.job_added = asyncio.Event()

	async def start(self):
		self.is_running = True
		asyncio.create_task(self._run())

	async def _run(self):
		while (self.is_running):
			await self.proc()

	async def stop(self):
		self.is_running = False

	async def proc(self):
		now = time.time()

		with self.jobs as jobs:
			ii = int()
			for ii, i in enumerate(jobs):
				if (now > i.at): break
				try: asyncio.create_task(i.call())
				except Exception as ex: raise # TODO, issue #16
			del jobs[:ii]

		if (jobs): await asyncio.sleep(max(jobs[0].at - int(time.time()) - 1, 0))
		else: await self.job_added.wait()

	async def add_job(self, job: Job):
		with self.jobs as jobs:
			bisect.insort(jobs, job)

		self.job_added.set()

# by Sdore, 2021-22
#  stbot.sdore.me
