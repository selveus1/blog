# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file for Likes functionality

from google.appengine.ext import db

# class to represent likes for a specific blog post
class Likes(db.Model):
	poster = db.StringProperty(required = True)
	blog_id = db.StringProperty(required = True)

	# check if a use liked a post already
	@classmethod
	def get_like_of_poster(cls, name):
		likes = Likes.all().filter('poster =', name).get()
		return likes

	# get total num of likes for a specific post
	@classmethod
	def get_num_likes(cls, blog_id):
		likes = Likes.all()
		likes = likes.filter('blog_id =', blog_id)

		if likes:
			return likes.count()

		return likes