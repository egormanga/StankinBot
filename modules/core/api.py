# StankinBot API core module

""" Модуль API
"""

from __future__ import annotations

import json, asyncio, datetime, functools
from aiohttp import web
from . import CoreModule
from ..utils import *

@export
class APIModule(CoreModule):
	events = []

	# public:
	unix: str

	# private:
	app: -- web.Application

	# internal:
	_runner: -- web.AppRunner
	_site: -- web.BaseSite

	async def init(self):
		app = self.app = web.Application(middlewares=(web.normalize_path_middleware(),))
		app.add_routes((
			web.get('/schedule/', self.handle_schedule),
			web.get('/schedule/groups/', self.handle_schedule_groups),
			web.get('/lecturer/find/', self.handle_lecturer_find),
		))

	async def start(self):
		runner = self._runner = web.AppRunner(self.app)
		await runner.setup()

		site = self._site = web.UnixSite(runner, self.unix)
		await site.start()

	async def stop(self):
		try: self._site
		except AttributeError: pass
		else: await self._site.stop()

		try: self._runner
		except AttributeError: pass
		else: await self._runner.cleanup()

	async def unload(self):
		del self.app, self._runner, self._site

	@staticmethod
	def ensure_get_params(query, *args):
		missing = tuple(i for i in args if not query.get(i))
		if (missing): raise web.HTTPBadRequest(reason=f"""{join_last((f"`{i}'" for i in missing), last=' and ')} parameter{' is' if (len(missing) == 1) else 's are'} required.""")
		return tuple(query[i] for i in args)

	async def handle_schedule(self, request):
		group, = self.ensure_get_params(request.query, 'group')

		async with self.bot.modules.backend.schedule.schedules as schedules:
			try: schedule = schedules[group.upper()]
			except KeyError: raise web.HTTPNotFound(reason="No schedule for this group.")

		return web.json_response(schedule.to_json(), dumps=functools.partial(json.dumps, ensure_ascii=False))

	async def handle_schedule_groups(self, request):
		async with self.bot.modules.backend.schedule.schedules as schedules:
			return web.json_response(tuple(schedules), dumps=functools.partial(json.dumps, ensure_ascii=False))

	async def handle_lecturer_find(self, request):
		name, date = self.ensure_get_params(request.query, 'name', 'date')
		name = name.casefold().strip().replace(' ', '.').rstrip('.')
		try:
			if (date == 'today'): date = datetime.date.today()
			elif (date == 'tomorrow'): date = (datetime.date.today() + datetime.timedelta(days=+1))
			else: date = datetime.date.fromisoformat(date)
		except ValueError as ex: raise web.HTTPBadRequest(reason="`date' parameter must be given in ISO 8601 date format or be one of `today', `tomorrow'.") from ex

		async with self.bot.modules.backend.schedule.schedules as schedules:
			pairs = tuple(i for schedule in schedules.values() for day in schedule.pairs for pair in day for i in pair if date in i.dates and name == (i.lecturer or '').casefold().strip().replace(' ', '.').rstrip('.'))

		return web.json_response(tuple(i.to_json() for i in pairs), dumps=functools.partial(json.dumps, ensure_ascii=False))

# by Sdore, 2022
# stbot.sdore.me
