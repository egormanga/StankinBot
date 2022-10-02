# StankinBot Telegram front-end

from __future__ import annotations

from . import *
from tgbot import *
from ..utils import *

class StankinTGBot(TGBot): pass
	### TODO
	#def error_callback(self, update, context):
	#	try: raise context.error
	#	except Unauthorized: raise
	#		# remove update.message.chat_id from conversation list
	#	except ChatMigrated as ex: raise
	#		# the chat_id of a group has changed, use ex.new_chat_id instead
	#	except Exception as ex: super().error_callback(update, context)
	###

@export
class TelegramFront(FrontendModule):
	name = 'telegram'
	events = []

	token: token[str]
	webhook: dict[unix: path[str], path: str, url: str]
	tgbot: -- TGBot

	def __init__(self, bot, webhook_port=None, webhook_path=None, webhook_url=None, **kwargs):
		super().__init__(bot, **kwargs)
		self.tgbot = StankinTGBot(self.token, webhook_port=webhook_port, webhook_path=webhook_path, webhook_url=webhook_url)

	async def init(self):
		self.bot.modules.frontend.multifront.register_front(self)

	async def start(self):
		self.tgbot.start()

	async def stop(self):
		self.tgbot.stop()

	async def unload(self):
		self.bot.modules.frontend.multifront.unregister_front(self)

	async def send(self, to, message):
		assert (to.front == self.name)
		return self.tgbot.bot.send_message(to.id, message.text)

	@classmethod
	def _message_handler(cls, f):
		return lambda update, context: f(User(cls.name, update.effective_user.id), Message(update.effective_message.text))

	def command(self, f):
		return self.tgbot.command(f.__name__)(self._message_handler(f))

	def command_unknown(self, f):
		return self.tgbot.command_unknown(self._message_handler(f))

	def message(self, f):
		return self.tgbot.message(Filters.text)(self._message_handler(f))

# by Sdore, 2021-22
#  stbot.sdore.me
