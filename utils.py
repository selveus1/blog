import re
import hmac


##########################
# Validatation Stuff
##########################
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

def valid_uname(u_name):
	return u_name and USER_RE.match(u_name)

def valid_pword(p_word):
	return p_word and PASS_RE.match(p_word)

def same_pwords(p_word, v_p_word):
	return p_word == v_p_word

def valid_email(email):
	return EMAIL_RE.match(email)


##################
# Cookie Methods
##################

cookie_hash = "13ifks.h/e?>{|W543kgfdl/s;klfsdgwe-=;',."
def hash_str(s):
	return hmac.new(cookie_hash, s).hexdigest()

def make_secure_val(s):
	return "%s|%s" % (s, hash_str(s))

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val



####################
# Password Hashing
####################
password_hash = "897345q!^%*{:FD90'.[mLHGyejfdlhjl;wrn"
def hash_pword(s):
	return hmac.new(password_hash, s).hexdigest()

def check_hash_pword(entered, stored):
	entered  = hash_pword(entered)
	return  entered == stored