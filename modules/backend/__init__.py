# StankinBot Backend module base class

""" Бэкенд
Модули обработки данных или взаимодействия с внешними сервисами.
"""

from .. import Module
from ..utils import *

@export
class BackendModule(Module):
	log_color = 91

# by Sdore, 2021-22
#  stbot.sdore.me
