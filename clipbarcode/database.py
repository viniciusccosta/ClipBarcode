from peewee import SqliteDatabase

from clipbarcode.utils import resource_path

db = SqliteDatabase(resource_path("database.db"))
