# StankinBot Schedule backend module

from __future__ import annotations

import io, re, bs4, math, tabula, urllib, aiohttp, asyncio, datetime, operator, functools, itertools, traceback, collections
from . import BackendModule
from ..core.database import databased
from ..utils import *

class Schedule(XABC):
	class Pair(XABC):
		class Location(XABC):
			room: str

			# properties:
			floor: -- int | None

			def to_json(self):
				return {
					'room': self.room,
					'floor': self.floor,
					#'building': self.building, # XXX
				}

			@property
			def floor(self) -> int | None:
				if (self.room.startswith('ИГ-')): return 4
				try: return int(self.room.lstrip('0')[0])
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
		lecturer: str | None
		location: Location
		group: Group
		time: (datetime.time, datetime.time)
		breaks: [(datetime.time, datetime.time)]
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
					'breaks': tuple({'start': s.strftime('%H:%M'), 'end': e.strftime('%H:%M')}
					                for s, e in self.breaks),
				},
				'dates': tuple(map(datetime.date.isoformat, self.dates)),
			}

		@staticmethod
		def parse_breaks(times: [(datetime.time, datetime.time)]) -> [(datetime.time, datetime.time)]:
			res = list()

			lastend = None
			for start, end in times:
				if (lastend is not None): res.append((lastend, start))
				t = datetime.datetime(1, 1, 1, start.hour, start.minute, start.second)
				e = datetime.datetime(1, 1, 1, end.hour, end.minute, end.second)
				while ((t := t + datetime.timedelta(minutes=+45)) < e):
					res.append((t.time(), (t := t + datetime.timedelta(minutes=+10)).time()))
				lastend = end

			return res

		@staticmethod
		def parse_dates(s: str, /, *, year=datetime.date.today().year) -> [datetime.date]:
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
		def from_str(cls, s: str, /, *, group: str, times):
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
			subgroup = (m['subgroup'] or None)
			room = m['room']
			time = (times[0][0], times[-1][1])
			breaks = cls.parse_breaks(times)
			dates = cls.parse_dates(m['dates'])

			location = cls.Location(room=room)
			group = cls.Group(group=group, subgroup=subgroup)

			return cls(name=name, type=type, lecturer=lecturer, location=location, group=group, time=time,
			           breaks=breaks, dates=dates)

	group: str
	pairs: [[[Pair]]]

	def __ior__(self, other):
		for day_a, day_b in zip(self.pairs, other.pairs):
			for pair_a, pair_b in zip(day_a, day_b):
				for i in pair_b:
					bisect.insort(pair_a, i, key=operator.attrgetter('time'))

		return self

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
		times = tuple(tuple(map(lambda x: datetime.time(*map(int, x.split(':'))), i['text'].split('-', maxsplit=1)))
		              for i in times[1:])

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
						p.add(cls.Pair.from_str(t+br, group=group, times=times[ii:ii+width]))

				for o in range(width):
					pairs[wd-1][ii+o] |= p

		pairs = tuple(pairs.values())

		return cls(group=group, pairs=pairs)

class ExamSchedule(Schedule):
	class ExamPair(Schedule.Pair):
		def __init__(self, *args, type='экзамен', date, **kwargs):
			super().__init__(*args, type=type, breaks=[], dates=[date], **kwargs)

		@property
		def date(self):
			return only(self.dates)

		@classmethod
		def from_str(cls, s: str, /, *, name: str, lecturer: str, group: str, date: datetime.date):
			m = re.match(r'''
				\s*(?P<from>\d+:\d+)
				\s*-?
				\s*(?P<to>\d+:\d+)
				\s*(?P<room>.+)
			''', s, re.X)

			time = tuple(map(lambda x: datetime.time(*map(int, x.split(':'))), (m['from'], m['to'])))
			room = m['room']

			location = cls.Location(room=room)
			group = cls.Group(group=group, subgroup=None)

			return cls(name=name, type=type, lecturer=lecturer, location=location, group=group, time=time, date=date)

	class ConsultationPair(ExamPair):
		def __init__(self, *args, type='консультация', **kwargs):
			super().__init__(*args, type=type, **kwargs)

		@classmethod
		def from_str(cls, s: str, /, *, name: str, lecturer: str, group: str):
			m = re.match(r'''
				\s*(?P<type>\w+):\s*
				\s*(?P<date>\d+\.\d+\.\d+)
				\s*(?P<time>\d+:\d+)
				\s*(?P<room>.+)
			''', s, re.X)

			type = m['type']
			date = datetime.datetime.strptime(m['date'], '%d.%m.%Y').date()
			time = (datetime.time(*map(int, m['time'].split(':'))),)*2
			room = m['room']

			location = cls.Location(room=room)
			group = cls.Group(group=group, subgroup=None)

			return cls(name=name, type=type, lecturer=lecturer, location=location, group=group, time=time, date=date)

	exams: [ExamPair]
	consultations: [ConsultationPair]

	@property
	def pairs(self):
		return tuple([[i] for i in v] for k, v in sorted(itertools.groupby(itertools.chain(self.exams, self.consultations), key=lambda x: x.date.weekday()), key=operator.itemgetter(0)))

	@classmethod
	def from_table(cls, group, table) -> ExamSchedule:
		exams = list()
		consultations = list()

		for consultation, exam, subject in groupby(table, 3):
			name = subject[1]['text'].strip()
			try: lecturer = (exam[2]['text'].strip().rstrip('.') + '.')
			except IndexError: lecturer = None # TODO FIXME?
			date = datetime.datetime.strptime(exam[0]['text'].strip(), '%d.%m.%Y').date()

			exams.append(cls.ExamPair.from_str(exam[1]['text'].strip(), name=name, lecturer=lecturer, group=group, date=date))
			consultations.append(cls.ConsultationPair.from_str(consultation[2]['text'].strip(), name=name, lecturer=lecturer, group=group))

		return cls(group=group, exams=exams, consultations=consultations)

@export
class ScheduleModule(BackendModule):
	events = []
	schedule_course_id = 11557

	# persistent:
	@databased('cache')
	class schedules(dict): schedules: dict[str -- group, Schedule]

	async def init(self):
		async with self.schedules as schedules:
			if (not schedules): del self.schedules

	async def get_schedule_folder_ids(self) -> [course_id[int]]:
		page = await self.bot.modules.backend.edu_api.get_course(self.schedule_course_id)
		topics = page.find(class_='topics').find_all('li', {'role': 'region'})
		ids = tuple(urllib.parse.urlparse(j['href']).query.partition('id=')[2]
		            for i in topics if 'Расписание занятий' in i.strings
		            for j in i.find_all() if j.get('href') is not None)
		return ids

	async def get_schedule_urls(self) -> dict[str -- group, str -- url]:
		ids = await self.get_schedule_folder_ids()
		urls = dict()
		for i in ids:
			page = await self.bot.modules.backend.edu_api.get_folder(i)
			urls |= {k: i['href'] for i in page.find_all('a') if (k := i.text.strip().rpartition('.pdf')[0].upper())}
		return urls

	@staticmethod
	def _read_pdf(f, lattice=True, stream=False):
		return tabula.read_pdf(f, output_format='json', pages='all', multiple_tables=False, lattice=lattice, stream=stream)

	async def get_schedule(self, group, url) -> Schedule:
		url = url.removeprefix(self.bot.modules.backend.edu_api.base_url)

		async with self.bot.modules.backend.edu_api.session.get(url) as r:
			content = await r.read()

		loop = asyncio.get_event_loop()
		with io.BytesIO(content) as f:
			data = await loop.run_in_executor(None, self._read_pdf, f)

		table = only(i['data'] for i in data)

		if ('консультация' in table[0][1]['text']):
			with io.BytesIO(content) as f:
				data = await loop.run_in_executor(None, functools.partial(self._read_pdf, lattice=False, stream=True), f)

			table = only(i['data'] for i in data)

			return ExamSchedule.from_table(group, table)

		return Schedule.from_table(group, table)

	@schedules.cached_getter(days=1)
	async def load_schedules(self) -> dict[str -- group, Schedule]:
		self.log("Loading schedules…")
		with timecounter() as tc:
			urls = await self.get_schedule_urls()
			self.log(f"Got schedule urls in {round(tc.time, 1)} sec.")
			schedules = await asyncio.gather(*itertools.starmap(self.get_schedule, urls.items()),
			                                 return_exceptions=True)
		self.log(f"Schedules loaded in {round(tc.time, 1)} sec.")

		res = dict()
		for i in schedules:
			if (isinstance(i, Exception)):
				print(f"Failed to parse schedule: {format_exc(i)}"); traceback.print_exception(i)
				continue
			try: sched = res[i.group]
			except KeyError: res[i.group] = i
			else: sched |= i

		return res

# by Sdore, 2022
# stbot.sdore.me
