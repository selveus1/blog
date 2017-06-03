# Author : Sheena Elveus
# Date: May 17 2017
# Description : Main Python file to generate blog site

import os
import jinja2
import webapp2
import datetime

from utils import *
from models.user import *
from models.blogpost import *
from models.comment import *
from models.likes import *
from models.unlikes import *
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

COOKIE_ID = 'id'


############
# Handlers
############
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_blog_pg(self, user, post, error=""):
        post_id = str(post.key().id())

        # load comments for a specific post
        comments = db.GqlQuery("SELECT * FROM Comment WHERE blog = :1 ORDER BY created DESC",
                               post_id)
        likes = Likes.get_num_likes(post_id)
        unlikes = Unlikes.get_num_unlikes(post_id)

        self.render("blog_post.html", post_id=post.key().id(), user=user, blog_post=post, likes=likes,
                    unlikes=unlikes, comments=comments, error=error)

    # create a cookie for a valid user
    def create_cookie(self, cookie_val):
        cookie = make_secure_val(cookie_val)
        self.response.headers.add_header('Set-Cookie',
                                         '%s=%s; Path=/' % (COOKIE_ID, cookie))

    # delete a cook for a user
    def delete_cookie(self):
        self.response.headers.add_header('Set-Cookie',
                                         '%s=; Path=/' % COOKIE_ID)

    def get_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # get the user currently logged in
    def get_user_from_cookie(self):
        cookie = self.request.cookies.get(COOKIE_ID)
        if cookie:
            user_id = str(cookie).split('|')[0]
            user = User.get_user_by_id(long(user_id))
            return user
        return None


class BaseHandler(Handler):
    def get(self):
        self.render("base.html")


class RegistrationHandler(Handler):
    def add_user_to_db(self, username, password, email=None):
        password = hash_pword(password)

        # check if username already taken
        is_taken = User.get_user_by_name(username)
        if is_taken:
            error = "That username already exists."
            self.render("registration.html", uname_error=error)
        else:
            # create user, set a cookie, and redirect to welcome page
            user = User(parent=user_key(), username=username,
                        password=password, email=email)
            user.put()
            self.create_cookie(str(user.key().id()))
            self.redirect("/welcome")

    def get_errors(self, choice):
        # catalogue errors from user registration
        errors = {"uname_error": "That is not a valid username.",
                  "pword_error": "That is not a valid password.",
                  "verify_error": "Your passwords don't match.",
                  "email_error": "That's not a valid email."}

        return errors[choice]

    def get(self):
        self.render("registration.html")

    def post(self):
        params = {}
        error = False

        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        if not valid_uname(username):
            params['uname_error'] = self.get_errors("uname_error")
            error = True

        if not valid_pword(password):
            params['pword_error'] = self.get_errors("pword_error")
            error = True

        if not same_pwords(password, verify):
            params['verify_error'] = self.get_errors("verify_error")
            error = True

        if email and not valid_email(email):
            params['email_error'] = self.get_errors("email_error")
            error = True

        if error:
            params['username'] = username
            params['email'] = email
            self.render("registration.html", **params)
        else:
            self.add_user_to_db(username, password, email)


class LoginHandler(Handler):
    def verify_login(self, username, password):
        # check if login info is correct
        user = User.get_user_by_name(username)

        if user:
            pword = check_hash_pword(password, user.password)

            if pword:
                return user

    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        user = self.verify_login(username, password)

        if user:
            self.create_cookie(str(user.key().id()))
            self.redirect("/welcome")
        else:
            incorrect = "That username / password combination was incorrect."
            self.render("login.html", error=incorrect)


class WelcomeHandler(Handler):
    def get(self):
        user = self.get_user_from_cookie()
        redirect = "<meta http-equiv=\"refresh\" content=\"2; url=/blog\"/>"
        self.render("welcome.html", user=user,
                    redirect=redirect, username=user.username)


class MainPage(Handler):
    def get(self):
        user = self.get_user_from_cookie()

        # valid user, load posts
        if user:
            posts = BlogPost.all().order('-created')

            if posts and posts.count() > 0:
                self.render("front.html", posts=posts, user=user)
            else:
                no_posts = "No Posts Written"
                self.render("front.html", no_posts=no_posts, user=user)
        else:
            # not logged in, redirect to front page
            self.redirect("/")


class LogoutHandler(Handler):
    def get(self):
        self.delete_cookie()
        self.render("logout.html")


class BlogPostHandler(Handler):
    def add_comment(self, user, post):
        if user.username == post.poster:
            error = "You can not comment on your own post."
            self.render_blog_pg(user, post, error)
        else:
            self.redirect("/newcomment/%s" % str(post.key().id()))

    def get(self, blog_id):
        user = self.get_user_from_cookie()

        # valid user
        if user:
            post = BlogPost.get_blog_by_id(long(blog_id))

            if post:
                post.readable_created = post.created.strftime("%A, %B %d %Y")
                self.render_blog_pg(user, post)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")

    def post(self, blog_id):
        # check if user is editing/deleting their own post
        user = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        if user:
            if post:

                if self.request.get("add-comment"):
                    self.add_comment(user, post)
            else:
                error = "No blog with that id!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")


class NewPostHandler(Handler):
    def get(self):
        user = self.get_user_from_cookie()

        if user:
            self.render("new_post.html", user=user)
        else:
            self.redirect("/")

    def post(self):
        user = self.get_user_from_cookie()

        subject = self.request.get("subject")
        content = self.request.get("content")

        # logged in user
        if user:
            # user entered subject and content
            if subject and content:
                user = self.get_user_from_cookie()
                i = datetime.datetime.now().strftime("%A, %B %d %Y")
                bp = BlogPost(parent=blog_key(), subject=subject,
                              content=content, poster=user.username,
                              readable_created=i)
                bp.put()
                bp.link_key = "/blog/%s" % str(bp.key().id())
                bp.put()
                self.redirect("/blog/%s" % str(bp.key().id()))
            else:
                error = "Subject and content!!!"
                self.render("new_post.html", subject=subject,
                            content=content, error=error)
        else:
            # not logged in user
            self.redirect("/")


class EditPostHandler(Handler):
    def get(self, blog_id):
        user = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        if user:
            if post:
                if user.username == post.poster:
                    self.render("edit_blog_post.html", user=user,
                                blog_post=post, blog_id=str(post.key().id()))

                else:
                    comments = Comment.get_comments_by_blog_id(str(blog_id))
                    likes = Likes.get_num_likes(str(blog_id))
                    unlikes = Unlikes.get_num_unlikes(str(blog_id))

                    error = "You can not edit someone else's post."
                    self.render("blog_post.html", post_id=blog_id, user=user,
                                blog_post=post, likes=likes, unlikes=unlikes,
                                comments=comments, error=error)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")

    def post(self, blog_id):
        user = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        if user:
            if post:
                if user.username == post.poster:
                    subject = self.request.get("edit-subject")
                    content = self.request.get("edit-content")
                    i = datetime.datetime.now().strftime("%A, %B %d %Y")
                    post.subject = subject
                    post.content = content
                    post.readable_created = i
                    post.put()
                    self.redirect(post.link_key)
                else:
                    error = "You can not edit someone else's post."
                    self.render("blog_post.html", user=user,
                                blog_post=post, error=error)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")


class DeletePostHandler(Handler):
    def get(self, blog_id):
        logged_in = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        if logged_in:
            comments = Comment.get_comments_by_blog_id(str(blog_id))
            likes = Likes.get_num_likes(str(blog_id))
            unlikes = Unlikes.get_num_unlikes(str(blog_id))

            # user can delete this post because they wrote it
            if logged_in.username == post.poster:

                if post:
                    post.delete()
                    self.redirect("/blog")
                else:
                    error = "No blog with that id!"
                    self.render("front.html", error=error)
            else:
                error = "You can not delete someone else's post."
                self.render("blog_post.html", post_id=blog_id,
                            user=logged_in, blog_post=post, likes=likes,
                            unlikes=unlikes, comments=comments, error=error)
        else:
            self.redirect("/")


class LikePostHandler(Handler):
    def get(self, blog_id):
        print
        "like"

        logged_in = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        # valid user
        if logged_in:

            if post:
                if logged_in.username == post.poster:
                    error = "You can not like your own post."
                    self.render_blog_pg(logged_in, post, error)
                else:
                    # user can like this post because they didn't write it
                    has_liked = Likes.get_like_of_poster(logged_in.username)
                    if has_liked:
                        error = "You've already liked this post."
                        self.render_blog_pg(logged_in, post, error)
                    else:
                        # if user unliked already, remove the unlike and then like
                        has_unliked = Unlikes.get_unlike_of_poster(logged_in.username)
                        if has_unliked:
                            has_unliked.delete()

                        like = Likes(poster=logged_in.username,
                                     blog_id=str(post.key().id()))
                        like.put()
                        self.render_blog_pg(logged_in, post)
                        self.redirect(post.link_key)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")


class UnlikePostHandler(Handler):
    def get(self, blog_id):
        print
        "unlike"

        logged_in = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        # valid user
        if logged_in:

            if post:
                if logged_in.username == post.poster:
                    error = "You can not unlike your own post."
                    self.render_blog_pg(user, post, error)
                else:
                    has_unliked = Unlikes.get_unlike_of_poster(logged_in.username)

                    if has_unliked:
                        error = "You've already unliked this post."
                        self.render_blog_pg(logged_in, post, error)
                    else:
                        # if user liked already, remove the like and then unlike
                        has_liked = Likes.get_like_of_poster(logged_in.username)
                        if has_liked:
                            has_liked.delete()

                        unlike = Unlikes(poster=logged_in.username,
                                         blog_id=str(post.key().id()))
                        unlike.put()
                        self.render_blog_pg(logged_in, post)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")


class NewCommentHandler(Handler):
    def get(self, blog_id):
        user = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        # logged in user
        if user:

            if post:
                self.render("new_comment.html", user=user,
                            blog_post=post, blog_id=str(blog_id))
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")

    def post(self, blog_id):
        user = self.get_user_from_cookie()
        post = BlogPost.get_blog_by_id(long(blog_id))

        # logged in user
        if user:
            if post:
                remark = self.request.get("remark")
                if remark:
                    i = datetime.datetime.now().strftime("%d/%m/%y @ %H:%M")
                    comment = Comment(parent=comment_key(),
                                      poster=user.username, remark=remark,
                                      blog=str(post.key().id()), readable_created=i)
                    comment.put()
                    comment.link_key = str(comment.key().id())
                    comment.put()
                    self.render_blog_pg(user, post)
                else:
                    error = "Add a comment please!!!"
                    self.render("new_comment.html", error=error, user=user,
                                blog_post=post, blog_id=str(blog_id))
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)

        else:
            self.redirect("/")


class EditCommentHandler(Handler):
    def get(self, comment_id):
        comment = Comment.get_comment_by_id(long(comment_id))
        user = User.get_user_by_name(comment.poster)
        post = BlogPost.get_blog_by_id(long(comment.blog))

        logged_in = self.get_user_from_cookie()
        # logged in user
        if logged_in:

            if post:

                # user editing their own comment
                if user.username == logged_in.username:
                    self.render("edit_comment.html", user=user,
                                blog_post=post, comment=comment,
                                blog_id=str(post.key().id()))
                else:
                    error = "You cannot edit this comment."
                    self.render_blog_pg(logged_in, post, error)
            else:
                error = "No blog with that ID!"
                self.render("front.html", error=error)
        else:
            self.redirect("/")

    def post(self, comment_id):
        comment = Comment.get_comment_by_id(long(comment_id))
        logged_in = self.get_user_from_cookie()

        # logged in user
        if logged_in:

            # comment doesn't exist
            if comment is None:
                error = "That comment doesn't exist!"
                self.render_blog_pg(logged_in, post, error)

            # else : comment exists
            user = User.get_user_by_name(comment.poster)
            post = BlogPost.get_blog_by_id(long(comment.blog))

            if user.username == logged_in.username:
                remark = self.request.get("edit-comment")

                if remark:
                    comment.poster = user.username
                    comment.remark = remark
                    comment.blog = str(post.key().id())
                    comment.put()
                    comment = Comment.get_comment_by_id(long(comment_id))
                    self.render_blog_pg(user, post)
                else:
                    error = "Add comments please!!"
                    self.render("edit_comment.html", user=user,
                                blog_post=post, comment=comment,
                                blog_id=str(post.key().id()), error=error)
            else:
                error = "You cannot edit this comment."
                self.render_blog_pg(logged_in, post, error)
        else:
            self.redirect("/")


class DeleteCommentHandler(Handler):
    def get(self, comment_id):
        comment = Comment.get_comment_by_id(long(comment_id))
        logged_in = self.get_user_from_cookie()

        # logged in user
        if logged_in:

            if comment is None:
                error = "Comment doesn't exist."
                self.render_blog_pg(logged_in, post, error)

            # else: comment exists
            user = User.get_user_by_name(comment.poster)
            post = BlogPost.get_blog_by_id(long(comment.blog))

            if comment:
                if logged_in.username == user.username:
                    comment.delete()
                    self.redirect("/blog/%s" % str(post.key().id()))
                else:
                    error = "You cannot delete this comment."
                    self.render_blog_pg(logged_in, post, error)
            else:
                error = "Comment no longer exists!"
                self.render_blog_pg(logged_in, post, error)
        else:
            self.redirect("/")


app = webapp2.WSGIApplication([('/', BaseHandler),
                               ('/register', RegistrationHandler),
                               ('/login', LoginHandler),
                               ('/welcome', WelcomeHandler),
                               ('/logout', LogoutHandler),
                               ('/blog', MainPage),
                               ('/blog/(\d+)', BlogPostHandler),
                               ('/blog/newpost', NewPostHandler),
                               ('/blog/edit/(\d+)', EditPostHandler),
                               ('/blog/delete/(\d+)', DeletePostHandler),
                               ('/blog/like/(\d+)', LikePostHandler),
                               ('/blog/unlike/(\d+)', UnlikePostHandler),
                               ('/newcomment/(\d+)', NewCommentHandler),
                               ('/editcomment/(\d+)', EditCommentHandler),
                               ('/deletecomment/(\d+)', DeleteCommentHandler),
                               ], debug=True)

