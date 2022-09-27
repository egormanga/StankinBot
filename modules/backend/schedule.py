# StankinBot Schedule backend module

from __future__ import annotations

import io, bs4, tabula, urllib, aiohttp, traceback
from . import BackendModule
from ..utils import *

class Schedule(XABC):
	pairs: [(time[str], time[str])]
	table: [[str]]

	def __init__(self, pairs, table):
		super().__init__(pairs=pairs, table=table)

	def to_json(self):
		return {
			'pairs': self.pairs,
			'table': self.table,
		}

@export
class ScheduleModule(BackendModule):
	events = []
	schedule_course_id = 11557

	# public:
	schedules: -- dict[str -- group, Schedule]

	def __init__(self, bot, **kwargs):
		super().__init__(bot, **kwargs)
		self.schedules = dict()

	async def init(self):
		self.schedules = await self.load_schedules()
		print(tuple(self.schedules))

	async def get_schedule_folder_ids(self) -> [course_id[int]]:
		page = await self.bot.modules.backend.edu_api.get_course(self.schedule_course_id)
		topics = page.find(class_='topics').find_all('li', {'role': 'region'})
		ids = tuple(urllib.parse.urlparse(j['href']).query.partition('id=')[2] for i in topics if 'Расписание занятий' in i.strings for j in i.find_all() if j.get('href') is not None)
		return ids

	async def get_schedule_urls(self) -> dict[str -- group, str -- url]:
		ids = await self.get_schedule_folder_ids()
		urls = dict()
		for i in ids:
			page = await self.bot.modules.backend.edu_api.get_folder(i)
			urls |= {i.text.strip().rpartition('.pdf')[0].upper(): i['href'] for i in page.find_all('a')}
			break # XXX
		return urls

	async def load_schedules(self) -> dict[str -- group, Schedule]:
		urls = await self.get_schedule_urls()
		schedules = dict()
		for group, url in urls.items():
			url = url.replace(self.bot.modules.backend.edu_api.base_url, '')
			async with self.bot.modules.backend.edu_api.session.get(url) as r:
				content = await r.read()

			with io.BytesIO(content) as f:
				try: data = sum((i['data'] for i in tabula.read_pdf(f, lattice=True, pages='all', output_format='json')), start=[])
				except Exception as ex: print(f"Failed to parse schedule for group {group}: {format_exc(ex)}"); traceback.print_exc(); continue

			pairs, *table = [[col['text'].strip().replace('\r', ' ') for col in row[1:]] for row in data]
			pairs = tuple(tuple(map(str.strip, i.split('-'))) for i in pairs)
			schedules[group] = Schedule(pairs, table)
		return schedules

# by Sdore, 2022
# stbot.sdore.me
