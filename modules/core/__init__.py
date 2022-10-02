# StankinBot Core module base class

""" Ядро
Основная часть бота, объединяющая все модули воедино.
"""

from .. import Module
from ..utils import *

@export
class CoreModule(Module):
	log_color = 93

# by Sdore, 2021-22
#  stbot.sdore.me
