# StankinBot Schedule backend module

from __future__ import annotations

import io, re, bs4, math, tabula, urllib, aiohttp, datetime, traceback, collections
from . import BackendModule
from ..utils import *

class Schedule(XABC):
	class Pair(XABC):
		class Location(XABC):
			room: str

			def to_json(self):
				return {
					'room': self.room,
					'floor': self.floor,
					#'building': self.building, # XXX
				}

			@property
			def floor(self) -> int | None:
				if (self.room.startswith('ИГ-')): return 4
				try: int(self.room.lstrip('0')[0])
				except ValueError: return None

		class Group(XABC):
			group: str
			subgroup: str | None

			def to_json(self):
				return {
					'group': self.group,
					'subgroup': self.subgroup,
				}

		name: str
		type: str
		lecturer: str
		location: Location
		group: Group
		time: (datetime.time, datetime.time)
		dates: [datetime.date]

		def to_json(self):
			return {
				'name': self.name,
				'type': self.type,
				'lecturer': self.lecturer,
				'location': self.location.to_json(),
				'group': self.group.to_json(),
				'time': {
					'start': self.time[0].strftime('%H:%M'),
					'end': self.time[1].strftime('%H:%M'),
				},
				'dates': tuple(map(datetime.date.isoformat, self.dates)),
			}

		@staticmethod
		def parse_dates(s, *, year=datetime.date.today().year) -> [datetime.date]:
			res = list()

			for i in s.casefold().split(','):
				f, _, t = i.partition('-')
				f = tuple(map(int, f.split('.')))
				f = datetime.date(year + (f[1] < 9), *f[::-1])

				if (not t): res.append(f); continue

				t, _, wd = t.partition(' ')
				t = tuple(map(int, t.split('.')))
				t = datetime.date(year + (t[1] < 9), *t[::-1])

				wd = wd.replace('.', '')

				ii = int()
				while (f <= t):
					if (ii % 2 == 0 or wd != 'чн'):
						res.append(f)
					f += datetime.timedelta(weeks=+1)

			return res

		@classmethod
		def from_str(cls, s, group, time):
			name = s

			m = re.match(r'''
				\s*(?P<name>.+?)\.
				\s*(?:(?P<lecturer>[\w .]+)\.)?
				\s*(?P<type>[\w ]+)\.
				\s*(?:\((?P<subgroup>\w)\)\.)?
				\s*(?P<room>.+)\.
				\s*\[(?P<dates>.*)\]
			''', s, re.X)
			if (m is None): print(s)

			name = m['name']
			lecturer = (m['lecturer'].rstrip('.')+'.' if (m['lecturer']) else None)
			type = m['type']
			subgroup = m['subgroup'] or None
			room = m['room']
			dates = cls.parse_dates(m['dates'])

			location = cls.Location(room=room)
			group = cls.Group(group=group, subgroup=subgroup)

			return cls(name=name, type=type, lecturer=lecturer, location=location, group=group, time=time, dates=dates)

	group: str
	pairs: [[[Pair]]]

	def to_json(self):
		return {
			'pairs': [[[i.to_json() for i in pair] for pair in day] for day in self.pairs],
		}

	@classmethod
	def from_table(cls, group, table) -> Schedule:
		yoffs = tuple(int(only({top for i in day if (top := i['top'])})) for day in table)
		yoff = yoffs[0]
		ydiff = int()
		for i in range(1, len(yoffs)):
			ydiff = max(ydiff, (yoffs[-i] - yoffs[-i-1]))

		times, *table = table
		times = tuple(tuple(map(lambda x: datetime.time(*map(int, x.split(':'))), i['text'].split('-', maxsplit=1))) for i in times[1:])

		pairs = collections.defaultdict(lambda: [set() for _ in times])

		for day in table:
			wd = only({wd for i in day if (wd := math.ceil((int(i['top']) - yoff) / ydiff))})
			for ii, i in enumerate(day[1:]):
				width = round(i['width'] / 94)
				text = i['text'].replace('\r', '\n').strip()
				if (not text): continue
				else: assert (width > 0)

				p = set()
				s = str()
				for t in text.split('\n'):
					s += ' '+t
					if (']' in s):
						t, br, s = map(str.strip, s.partition(']'))
						p.add(cls.Pair.from_str(t+br, group, times[wd-1]))

				for o in range(width):
					pairs[wd-1][ii+o] |= p

		pairs = tuple(pairs.values())

		return cls(group=group, pairs=pairs)

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
			urls |= {k: i['href'] for i in page.find_all('a') if (k := i.text.strip().rpartition('.pdf')[0].upper())}
		return urls

	async def load_schedules(self) -> dict[str -- group, Schedule]:
		urls = await self.get_schedule_urls()
		schedules = dict()
		for group, url in urls.items():
			url = url.replace(self.bot.modules.backend.edu_api.base_url, '')
			async with self.bot.modules.backend.edu_api.session.get(url) as r:
				content = await r.read()

			with io.BytesIO(content) as f:
				try: data = only(i['data'] for i in tabula.read_pdf(f, output_format='json', pages='all', multiple_tables=False, lattice=True))
				except Exception as ex: print(f"Failed to read schedule pdf for group {group}: {format_exc(ex)}"); traceback.print_exc(); continue

			try: schedules[group] = Schedule.from_table(group, data)
			except Exception as ex: print(f"Failed to parse schedule for group {group}: {format_exc(ex)}"); traceback.print_exc(); continue
		return schedules

# by Sdore, 2022
# stbot.sdore.me
