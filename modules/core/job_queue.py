# StankinBot JobQueue core module

""" Модуль отложенных задач
См. https://github.com/egormanga/StankinBot/issues/15
"""

from __future__ import annotations

import bisect, asyncio, datetime
from . import CoreModule
from .database import databased
from ..utils import *

class Job(XABC):
	at: datetime.datetime
	before: datetime.datetime
	cancelled: bool
	call: code[str]

	def __init__(self, call, *, at=None, before=None, cancelled=False, **kwargs):
		if (at is None): at = datetime.datetime.now().astimezone()
		super().__init__(call=call, at=at, before=before, cancelled=cancelled, **kwargs)

	def __repr__(self):
		return f"<Job «{self.call}» at {self.at}{f' before {self.before}' if (self.before is not None) else ''}{' (cancelled)' if (self.cancelled) else ''}>"

	def __lt__(self, other):
		return (self.at < other.at)

	def cancel(self):
		self.cancelled = True

@export
class JobQueueModule(CoreModule):
	events = []

	# persistent:
	@databased('state')
	class jobs(list): jobs: sorted[[Job]]

	# public:
	initial: list[dict]

	# private:
	job_added: -- asyncio.Event

	# internal:
	_is_running: -- bool
	_task: -- asyncio.Task

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self._is_running = bool()
		self.job_added = asyncio.Event()

	async def init(self):
		for i in self.initial:
			await self.add_job(Job(**{k: (eval(str(v)) if (k != 'call') else str(v)) for k, v in i.items()}))

	async def start(self):
		self._is_running = True
		self._task = create_wrapped_task(self._run())

	async def _run(self):
		while (self._is_running):
			try: await self.proc()
			except asyncio.CancelledError:
				if (self._is_running): raise

	async def stop(self):
		self._is_running = False
		self.job_added.set()
		try: self._task.cancel()
		except AttributeError: pass
		else: await self._task

	async def proc(self):
		now = datetime.datetime.now().astimezone()

		self.job_added.clear()
		async with self.jobs as jobs:
			ii = -1
			for ii, i in enumerate(jobs):
				if (now < i.at): break
				if (not i.cancelled and (i.before is None or now < i.before)):
					try: create_wrapped_task(eval(f"(({i.call}) for _ in (None,) if _ is None or await _).__anext__()"))
					except Exception as ex: raise # TODO, issue #16
			else: ii += 1
			del jobs[:ii]

		if (jobs): await asyncio.sleep(max(int((jobs[0].at - datetime.datetime.now().astimezone()).total_seconds()), 0))
		else: await self.job_added.wait()

	async def add_job(self, job: Job):
		async with self.jobs as jobs:
			bisect.insort(jobs, job)

		self.job_added.set()

# by Sdore, 2021-22
#  stbot.sdore.me
