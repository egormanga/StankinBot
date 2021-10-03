# StankinBot StankinAPI backend module

from __future__ import annotations

import aiohttp
from . import BackendModule
from ..utils import *

class Categories(XABC):
	tree: Category
	buffer: [Category]

class Category(XABC):
	id: int
	name: str
	delta: text[dict]
	attachments: '?'
	chief_id: int
	employers: '?'
	config: bitfield[str]
	news: '?'
	announces: '?'
	docs: '?'
	parent: int
	childs: json[str]
	delta_history: json[str]
	num: int
	visible: bool
	important: {'user': dict, 'subdivisions': [dict]}

class Articles(XABC):
	news: [Article]
	count: int

class Article(XABC):
	id: int
	date: time[str]
	title: str
	short_text: str
	logo: url[str]
	tags: json[str]
	text: str
	author_id: int
	attachments: '?'
	subdivision_id: int
	pull_site: bool
	is_main: bool
	delta: {'ops': [dict]}

@export
class StankinAPIModule(BackendModule):
	events = []

	api_url = "https://stankin.ru/api_entry.php"

	async def _call(self, action, **data):
		async with aiohttp.request('POST', self.api_url, headers={'Content-Type': 'application/json'}, json={'action': action, 'data': data}) as r:
			r = await r.json()
		if (not r['success']): raise StankinAPIError(r['error'])
		return r['data']

	async def getNews(self, *, is_main=False, pull_site=False, subdivision_id=0, count=2**63-1, page=1, tag='', query_search=''):
		return Articles(**await self._call('getNews', is_main=is_main, pull_site=pull_site, subdivision_id=subdivision_id, count=count, page=page, tag=tag, query_search=query_search))

	async def getNewsItem(self, id):
		return Article(**await self._call('getNewsItem', id=id))

	async def getSubdivisions(self, *, tree=True, buffer=False):
		return Categories(**await self._call('getSubdivisions', tree=tree, buffer=buffer))

	async def getSubdivision(self, id):
		return Category(**await self._call('getSubdivision', id=id))

# by Sdore, 2021
# stbot.sdore.me