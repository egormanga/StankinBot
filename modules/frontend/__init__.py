# StankinBot Front module base class

""" Фронтенд
Модули взаимодействия с пользователем.
"""

from __future__ import annotations

import collections
from .. import Module
from ..utils import *

@export
class User(XABC):
	front: name[str]
	id: int

	def __init__(self, front, id: int, **kwargs):
		super().__init__(front=front, id=id, **kwargs)

@export
class Message(XABC):
	class Keyboard(XABC):
		pass # TODO

	id: int
	text: str
	keyboard: Keyboard | None

	def __init__(self, id: int, text: str, keyboard=None, **kwargs):
		super().__init__(id=id, text=text, keyboard=keyboard, **kwargs)

@export
class Conversation(XABC):
	state: (name[str], data[dict])

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
	log_color = 92

@export
class PlatformFrontendModule(FrontendModule):
	# attributes:
	name: str = ...

	# private:
	handlers: -- collections.defaultdict[list]

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.handlers = collections.defaultdict(list)

	def register_handler(self, event: str, h):
		self.handlers[event].append(h)

	def unregister_handler(self, event: str, h):
		self.handlers[event].remove(h)

	async def send(self, to: User, message: Message): ...

	async def send_mass(self, to: [User], message: Message):
		r = list()
		for i in to:
			try: r.append(await self.send(i, message))
			except Exception as ex: r.append(ex)
		return r

# by Sdore, 2021-22
#  stbot.sdore.me
