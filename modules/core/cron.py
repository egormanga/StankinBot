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
	before: time[float]
	cancelled: bool
	call: function

	def __init__(self, call, *, before=float('inf'), **kwargs):
		super().__init__(call=call, before=before, **kwargs)

	def __le__(self, other):
		return (self.at < other.at)

	def cancel(self):
		self.cancelled = True

@export
class CronModule(CoreModule):
	events = []

	# persistent:
	@databased
	class jobs(list): jobs: sorted[[Job]]

	# private:
	is_running: -- bool
	job_added: -- asyncio.Event

	# internal:
	_task: -- asyncio.Task

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.is_running = bool()
		self.job_added = asyncio.Event()

	async def start(self):
		self.is_running = True
		self._task = asyncio.create_task(self._run())

	async def _run(self):
		while (self.is_running):
			try: await self.proc()
			except asyncio.CancelledError:
				if (self.is_running): raise

	async def stop(self):
		self.is_running = False
		self.job_added.set()
		try: self._task.cancel()
		except AttributeError: pass
		else: await self._task

	async def proc(self):
		now = time.time()

		with self.jobs as jobs:
			ii = int()
			for ii, i in enumerate(jobs):
				if (now > i.at): break
				if (not i.cancelled and now < i.before):
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
