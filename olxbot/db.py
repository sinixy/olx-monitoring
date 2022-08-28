import sqlite3
from datetime import datetime


class Database:
	def __init__(self):
		self.connection = sqlite3.connect('data.db')
		self.cursor = self.connection.cursor()

	def create_filter(self, title, url):
		query = 'INSERT INTO Filter (title, url) VALUES (?, ?)'
		self.cursor.execute(query, (title, url.replace('/d/uk', '')))
		self.connection.commit()

	def get_all_filters(self):
		query = 'SELECT * FROM Filter'
		return [row for row in self.cursor.execute(query)]

	def get_filter(self, id):
		query = f'SELECT * FROM Filter WHERE id = {id}'
		self.cursor.execute(query)
		return self.cursor.fetchone()

	def update_filter_title(self, id, title):
		query = 'UPDATE Filter SET title = ? WHERE id = ?'
		self.cursor.execute(query, (title, id))
		self.connection.commit()

	def update_filter_link(self, id, link):
		query = 'UPDATE Filter SET url = ? WHERE id = ?'
		self.cursor.execute(query, (link.replace('/d/uk', ''), id))
		self.connection.commit()

	def delete_filter(self, id):
		query = f'DELETE FROM Filter WHERE id = {id}'
		self.cursor.execute(query)
		self.connection.commit()

	def get_adv(self, url):
		query = f'SELECT * FROM Filter WHERE id = {url}'
		self.cursor.execute(query)
		return self.cursor.fetchone()

	def get_today_adv(self):
		res = []
		query = 'SELECT * FROM adv'
		now = datetime.now()
		for row in self.cursor.execute(query):
			dt = datetime.strptime(row[2], '%d-%m-%Y %H:%M')
			if dt.year == now.year and dt.month == now.month and dt.day == now.day:
				res.append(row)
		return res

	def add_adv(self, url, title, dt):
		query = 'INSERT INTO adv (url, title, datetime) VALUES (?, ?, ?)'
		self.cursor.execute(query, (url, title, dt))
		self.connection.commit()

	def delete_adv(self, url):
		query = f'DELETE FROM adv WHERE url = {url}'
		self.cursor.execute(query)
		self.connection.commit()

	def clear_adv(self):
		query_get = 'SELECT * FROM adv'
		now = datetime.now()
		todel = []
		for row in self.cursor.execute(query_get):
			dt = datetime.strptime(row[2], '%d-%m-%Y %H:%M')
			if dt.year != now.year or dt.month != now.month or dt.day != now.day:
				todel.append( (row[0],) )
		query_clear = 'DELETE FROM adv WHERE url = ?'
		self.cursor.executemany(query_clear, todel)
		self.connection.commit()