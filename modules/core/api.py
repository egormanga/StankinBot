# StankinBot API core module

""" Модуль API
"""

from __future__ import annotations

import asyncio
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
	_site: -- web.UnixSite

	async def init(self):
		app = self.app = web.Application()
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
		try: self._runner
		except AttributeError: pass
		else: await self._runner.cleanup()

	async def handle_schedule(self, request):
		group = request.query.get('group')
		if (not group): raise web.HTTPBadRequest(reason="`group' parameter is required.")

		try: schedule = self.bot.modules.backend.schedule.schedules[group.upper()]
		except KeyError: raise web.HTTPNotFound(reason="No schedule for this group.")

		return web.json_response(schedule.to_json())

	async def handle_schedule_groups(self, request):
		return web.json_response(tuple(self.bot.modules.backend.schedule.schedules))

# by Sdore, 2022
# stbot.sdore.me
