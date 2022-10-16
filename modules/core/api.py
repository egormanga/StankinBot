# StankinBot API core module

""" Модуль API
"""

from __future__ import annotations

import json, asyncio, functools
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

	async def handle_schedule(self, request):
		group = request.query.get('group')
		if (not group): raise web.HTTPBadRequest(reason="`group' parameter is required.")

		async with self.bot.modules.backend.schedule.schedules as schedules:
			try: schedule = schedules[group.upper()]
			except KeyError: raise web.HTTPNotFound(reason="No schedule for this group.")

		return web.json_response(schedule.to_json(), dumps=functools.partial(json.dumps, ensure_ascii=False))

	async def handle_schedule_groups(self, request):
		async with self.bot.modules.backend.schedule.schedules as schedules:
			return web.json_response(tuple(schedules), functools.partial(json.dumps, ensure_ascii=False))

# by Sdore, 2022
# stbot.sdore.me
