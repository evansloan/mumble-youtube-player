import sqlite3

from bot.commands import *
from bot.mumblebot import MumbleBot

conn = sqlite3.connect('../users.db', check_same_thread=False)
