# StankinBot Cron core module

""" Модуль запланированных задач
См. https://github.com/egormanga/StankinBot/issues/14
"""

from __future__ import annotations

import time, asyncio, datetime
from . import CoreModule
from .database import databased
from .job_queue import Job
from ..utils import *

class Task(XABC):
	call: code[str]
	count: int | None

	def __init__(self, call, *, count=None, **kwargs):
		super().__init__(call=call, count=count, **kwargs)

	def __repr__(self):
		return f"<Task {self.call}{f' ({self.count} runs left)' if (self.count is not None) else ''}>"

class PeriodicTask(Task):
	interval: datetime.timedelta
	since: datetime.datetime | None
	until: datetime.datetime | None
	lastrun: datetime.datetime

	def __init__(self, call, interval, since=None, until=None, *, count=None, lastrun=None, **kwargs):
		if (since is None): since = datetime.datetime.now().astimezone()
		if (lastrun is None): lastrun = (since - interval)
		if (until is None and count is not None): until = (since + interval*(count+1)) # XXX +1?
		super().__init__(call=call, since=since, interval=interval, until=until, count=count, lastrun=lastrun, **kwargs)

	def __repr__(self):
		return f"<Task «{self.call}» since {self.since}{f' until {self.until}' if (self.until is not None) else ''} with interval {self.interval}{f' ({self.count} runs left)' if (self.count is not None) else ''}>"

class ConditionalTask(Task):
	events: tuple[str]
	after: datetime.datetime | None
	before: datetime.datetime | None

	def __init__(self, call, events, after=None, before=None, **kwargs):
		events = tuple(events)
		if (after is None): after = datetime.datetime.now().astimezone()
		super().__init__(call=call, events=events, after=after, before=before, **kwargs)

	def __repr__(self):
		return f"<Task {self.call} at events {self.events} after {self.after}{f' before {self.before}' if (self.before is not None) else ''}{f' ({self.count} runs left)' if (self.count is not None) else ''}>"

@export
class CronModule(CoreModule):
	events = []

	# persistent:
	@databased('state')
	class tasks(list): tasks: list[Task]
	@databased('state')
	class event_queue(asyncio.Queue): event_queue: asyncio.Queue[Task]

	# public:
	periodic: list[dict]
	conditional: list[dict]

	# internal:
	_static: -- list[Task]
	_is_running: -- bool
	_task: -- asyncio.Task

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self._static = list()
		self._is_running = bool()

	async def init(self):
		for i in self.periodic:
			task = await self.create_task(PeriodicTask(**{k: (eval(str(v)) if (k != 'call') else str(v)) for k, v in i.items()}))
			self._static.append(task)

		for i in self.conditional:
			task = await self.create_task(ConditionalTask(**{k: (eval(str(v)) if (k != 'call') else str(v)) for k, v in i.items()}))
			self._static.append(task)

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

		_task = self._task
		try: _task.cancel()
		except AttributeError: pass
		else: await _task

		async with self.tasks as tasks:
			for i in self._static:
				try: tasks.remove(i)
				except ValueError: pass

	async def proc(self):
		now = datetime.datetime.now().astimezone()

		async with self.tasks as tasks:
			for i in tasks.copy():
				if (isinstance(i, PeriodicTask)):
					if (now >= i.since and (i.until is None or now < i.until) and now >= (i.lastrun + i.interval)):
						while ((nextrun := (i.lastrun + i.interval)) < now):
							i.lastrun = nextrun
						before = (nextrun + i.interval)
						await self.bot.modules.core.job_queue.add_job(Job(i.call, at=nextrun, before=(min(before, i.until) if (i.until is not None) else before)))
						if (i.count is not None): i.count -= 1
					if ((i.count is not None and i.count <= 0) or
					    (i.until is not None and now >= i.until)): tasks.remove(i)

			async with self.event_queue as event_queue:
				while (True):
					try: event = event_queue.get_nowait()
					except asyncio.QueueEmpty: break

					for i in tasks.copy():
						if (isinstance(i, ConditionalTask)):
							if (event in i.events and (i.after is None or now >= i.after) and (i.before is None or now < i.before)):
								await self.bot.modules.core.job_queue.add_job(Job(i.call, before=i.before))
								if (i.count is not None): i.count -= 1
							if ((i.count is not None and i.count <= 0) or
							    (i.before is not None and now >= i.before)): tasks.remove(i)

		await asyncio.sleep(0.01) # XXX FIXME

	async def create_task(self, task: Task):
		async with self.tasks as tasks:
			if (task not in tasks):
				tasks.append(task)
			print(tasks) # XXX
		return task

	async def remove_task(self, task: Task):
		async with self.tasks as tasks:
			tasks.remove(task)

	async def handle_event(self, event: str):
		async with self.event_queue as event_queue:
			await event_queue.put(event)

# by Sdore, 2022
# stbot.sdore.me
