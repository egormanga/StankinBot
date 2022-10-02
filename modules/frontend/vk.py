# StankinBot VK front-end

from __future__ import annotations

import random, aiohttp, asyncio, collections
from aiohttp import web
from . import *
from ..utils import *

class VKUser(User):
	def __init__(self, *args, **kwargs):
		super().__init__(front=VKFront.name, *args, **kwargs)

@export
class VKFront(PlatformFrontendModule):
	# attributes:
	name = 'vk'
	events = []
	api_url = "https://api.vk.com"

	# public:
	token: str
	webhook: dict[unix: path[str], path: str, url: str]

	# private:
	app: -- web.Application

	# internal:
	_session: -- aiohttp.ClientSession
	_runner: -- web.AppRunner
	_site: -- web.BaseSite

	async def init(self):
		self._session = aiohttp.ClientSession(self.api_url, raise_for_status=True)
		app = self.app = web.Application()
		app.add_routes((
			web.post(self.webhook.path, self.handle),
		))
		self.bot.modules.frontend.multifront.register_front(self)

	async def start(self):
		runner = self._runner = web.AppRunner(self.app)
		await runner.setup()

		site = self._site = web.UnixSite(runner, self.webhook.unix)
		await site.start()

	async def stop(self):
		try: self._site
		except AttributeError: pass
		else: await self._site.stop()

		try: self._runner
		except AttributeError: pass
		else: await self._runner.cleanup()

	async def unload(self):
		self.bot.modules.frontend.multifront.unregister_front(self)
		await self._session.close()
		del self._session
		del self.app, self._runner, self._site

	async def handle(self, request):
		data = DictAttrProxy(await request.json())

		if (data.type == 'message_new'):
			m = data.object.message
			user = VKUser(m.from_id)
			message = Message(m.id, text=m.text)
			asyncio.create_task(self.mark_as_read(user, message))
			for h in self.handlers['message']:
				asyncio.create_task(h(user, message))
		else: print(data) # XXX

		return web.Response(text='OK')

	async def api(self, method, **data):
		data = ({'access_token': self.token, 'v': '5.131'} | data)
		async with self._session.post(f"/method/{method}", data=data) as r:
			res = await r.json()
		if ('error' in res): raise VKAPIError(res['error'], method, data)
		return DictAttrProxy(res)

	async def send(self, to: User, message: Message):
		assert (to.front == self.name)
		return await self.api('messages.send',
			peer_id = to.id,
			message = message.text,
			random_id = random.randrange(1 << 32),
		)

	async def send_mass(self, to: [User], message: Message):
		return await self.api('messages.send',
			peer_ids = tuple(i.id for i in to if assert_(i.front == self.name)),
			message = message.text,
			random_id = random.randrange(1 << 32),
		)

	async def mark_as_read(self, user: Peer, message: Message, mark_conversation_as_read=True, **kwargs):
		return await self.api('messages.markAsRead',
			peer_id = user.id,
			message_id = message.id,
			mark_conversation_as_read = mark_conversation_as_read,
			**kwargs
		)

class VKAPIError(Exception): pass

# by Sdore, 2021-22
#  stbot.sdore.me
