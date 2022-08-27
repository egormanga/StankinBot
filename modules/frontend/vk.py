# StankinBot VK front-end

from __future__ import annotations

from aiohttp import web
from . import *
from ..utils import *

class VKApi(XABC):
	api_url = "https://api.vk.com"

	token: str
	webhook_unix: str
	app: -- web.Application
	runner: -- web.AppRunner
	site: -- web.BaseSite

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app = web.Application()
		self.app.add_routes((web.post('/StankinBot', self.handle),))
		self.runner = web.AppRunner(self.app)
		self.site = None

	async def init(self):
		await self.runner.setup()
		self.site = web.UnixSite(self.runner, self.webhook_unix)

	async def start(self):
		await self.site.start()

	async def stop(self):
		await self.site.stop()

	async def unload(self):
		await self.runner.cleanup()
		self.site = None

	async def handle(self, request):
		print(request) # XXX
		return web.Response(text="OK")

	async def api(self, method, **data):
		data = ({'access_token': self.token, 'v': '5.131'} | data)
		async with aiohttp.request('POST', self.api_url+'/method/'+method, headers={'Content-Type': 'application/json'}, json=data) as r:
			res = await r.json()
		if ('error' in res): raise VKAPIError(res['error'], method, data)
		return DictAttrProxy(res['response'])

	async def send(self, peer_id, text):
		return await self.api('messages.send', peer_id=peer_id, message=text)

	async def send_mess(self, peer_ids, text):
		return await self.api('messages.send', peer_ids=peer_ids, message=text)

@export
class VKFront(FrontendModule):
	name = 'vk'
	events = []

	token: token[str]
	webhook: dict[unix: path[str], path: str, url: str]
	api: -- VKApi

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.api = VKApi(token=self.token, webhook_unix=self.webhook.unix)

	async def init(self):
		await self.api.init()

	async def start(self):
		await self.api.start()

	async def stop(self):
		await self.api.stop()

	async def unload(self):
		await self.api.unload()

	async def send(self, to, message):
		assert (to.front == self.name)
		return await self.api.send(to.id, message.text)

	async def send_mass(self, to, message):
		return await self.api.send_mass([i.id for i in to if assert_(i.front == self.name)], message.text)

	@classmethod
	def _message_handler(cls, f):
		return lambda update: f(User(cls.name, update.message.from_id), Message(update.message.text))

	def command(self, f):
		return self.api.command(f.__name__)(self._message_handler(f))

	def command_unknown(self, f):
		return self.api.command_unknown(self._message_handler(f))

	def message(self, f):
		return self.api.message(Filters.text)(self._message_handler(f))

# by Sdore, 2021-22
#  stbot.sdore.me
