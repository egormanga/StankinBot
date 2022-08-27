# StankinBot Front module base class

""" Фронтенд
Модули взаимодействия с пользователем.
"""

from __future__ import annotations

from .. import Module
from ..utils import *

class User(XABC):
	front: name[str]
	id: int

	def __init__(self, front, id: int):
		self.front, self.id = front, id

class Message(XABC):
	text: str

	def __init__(self, text: str):
		self.text = text

class Conversation(XABC):
	state: (state[str], data[dict])

	async def handle(self, message: Message) -> state:
		state, data = self.state
		handler = getattr(self, state)

		try: self.state = await handler(message, **data)
		except Exception as ex: logexception(ex); self.state = await self.error(message)
		finally:
			if (isinstance(self.state, str)): self.state = (self.state, {})
		return self.state

	async def start(self, message: Message) -> state: ...

	async def error(self, message: Message) -> state: ...

@export
class FrontendModule(Module):
	User = User

	async def send(self, to: User, message: Message): ...

	async def send_mass(self, to: [User], message: Message):
		r = list()
		for i in to:
			try: r.append(await self.send(i, message))
			except Exception as ex: r.append(ex)
		return r

	@decorator
	def command(self, f: callback(user[User], message[Message])): ...

	@decorator
	def command_unknown(self, f: callback(user[User], message[Message])): ...

	@decorator
	def message(self, f: callback(user[User], message[Message])): ...

	@abstractproperty
	def name(): ...

	#@classproperty
	#def name(cls):
	#	return cls.__module__.partition('frontend.')[2].partition('.')[0]

# by Sdore, 2021-22
#  stbot.sdore.me
