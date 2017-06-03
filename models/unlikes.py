# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file for Unlikes functionality

from google.appengine.ext import db

class Unlikes(db.Model):
	poster = db.StringProperty(required = True)
	blog_id = db.StringProperty(required = True)

	# check if a user has unliked a post
	@classmethod
	def get_unlike_of_poster(cls, name):
		unlikes = Unlikes.all().filter('poster =', name).get()
		return unlikes

	# get total num of unlikes for a specific post
	@classmethod
	def get_num_unlikes(cls, blog_id):
		unlikes = Unlikes.all()
		unlikes = unlikes.filter('blog_id =', blog_id)

		if unlikes:
			return unlikes.count()

		return unlikes