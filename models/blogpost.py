# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file for BlogPost functionality

from google.appengine.ext import db


def blog_key(name='default'):
	return db.Key.from_path('blogs', name)


class BlogPost(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	modified = db.DateTimeProperty()
	poster = db.StringProperty(required = True)
	readable_created = db.StringProperty()
	link_key = db.StringProperty()

	@classmethod
	def get_blog_by_id(cls, bid):
		return BlogPost.get_by_id(bid, parent = blog_key())

	@classmethod
	def get_blog_by_poster(cls, username):
		blog = BlogPost.all().filter('poster =', username).get()
		return blog