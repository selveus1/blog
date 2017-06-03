# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file for Comment functionality

from google.appengine.ext import db

def comment_key(name='default'):
	return db.Key.from_path('comments', name)

class Comment(db.Model):
	poster = db.StringProperty(required = True)
	remark = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)	
	readable_created = db.StringProperty()
	blog = db.StringProperty(required = True)
	link_key = db.StringProperty()

	@classmethod
	def get_comment_by_id(cls, cid):
		return Comment.get_by_id(cid, parent = comment_key())


	@classmethod
	def get_comments_by_blog_id(cls, bid):
		comments = Comment.all().order('-created')
		comments = comments.filter('blog =', bid)
		return comments

	@classmethod
	def get_comments_by_user(cls, username, bid):
		comment = Comment.all().filter('poster =', username)
		comment = comment.filter('blog =', bid ).get()
		return comment