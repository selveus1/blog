# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file for User functionality

from google.appengine.ext import db


def user_key(name='default'):
	return db.Key.from_path('users', name)


class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()

	@classmethod
	def get_user_by_id(cls, uid):
		return User.get_by_id(uid, parent = user_key())

	@classmethod
	def get_user_by_name(cls, name):
		user = User.all().filter('username =', name).get()
		return user