# StankinBot Stankin Edu backend module

from __future__ import annotations

import bs4, aiohttp, http.cookies
from . import BackendModule
from ..core.database import databased
from ..utils import *

@export
class StankinEduModule(BackendModule):
	events = []
	base_url = "https://edu.stankin.ru"
	schedule_course_id = 11557

	# persistent:
	@databased('cache')
	class cookies(dict): cookies: collections.defaultdict[http.cookies.BaseCookie]

	# public:
	username: str
	password: str

	# private:
	session: -- aiohttp.ClientSession

	async def init(self):
		self.session = aiohttp.ClientSession(self.base_url, raise_for_status=True)
		async with self.cookies as cookies:
			self.session.cookie_jar.update_cookies({k: v for k, v in cookies.items() if k})

	async def unload(self):
		#await self.logout()
		await self.session.close()
		del self.session

	@cookies.cached_getter(days=1)
	async def login(self):
		async with self.session.get("/login/index.php") as r:
			page = bs4.BeautifulSoup(await r.text(), 'html.parser')
		logintoken = page.find('input', {'name': 'logintoken'})['value']
		await self.session.post("/login/index.php", data={'username': self.username, 'password': self.password,
		                                                  'logintoken': logintoken})
		return self.session.cookie_jar._cookies

	async def logout(self):
		await self.session.get("/login/logout.php")

	async def get_course(self, course_id):
		async with self.session.get("/course/view.php", params={'id': course_id}) as r:
			page = bs4.BeautifulSoup(await r.text(), 'html.parser')
		main = page.find(class_='region-main')
		return main

	async def get_folder(self, folder_id):
		async with self.session.get("/mod/folder/view.php", params={'id': folder_id}) as r:
			page = bs4.BeautifulSoup(await r.text(), 'html.parser')
		main = page.find(class_='region-main')
		return main

# by Sdore, 2022
# stbot.sdore.me
