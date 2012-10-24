import hashlib
import json
import webapp2
import random
import string
import jinja2
import os
import logging

jinja_environment = jinja2.Environment(autoescape=True,
                                       loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


def check_custom_path_hash(custompath, hash):
    # sha(custompath) = hash?
    # and add salt
    return True


def check_cookie(cookie_string):
    try:
        user_id, hash_value, salt = cookie_string.split("|")
    except ValueError:
        # after was "somehow changed", dont allow login
        return None

    logging.info("user_id: %s, hash_value: %s, salt: %s" % (user_id, hash_value, salt))
    if make_hash(user_id, salt) == cookie_string:
        return user_id
    else:
        return None


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_hash(user_id, salt):
    h = hashlib.sha256(salt + user_id + salt).hexdigest()
    return "%s|%s|%s" % (user_id, h, salt)

def make_pw_hash(pw, salt):
    h = hashlib.sha256(pw + salt).hexdigest()
    return "%s|%s" % (h, salt)

def hash_pw_for_db(pw):
    salt = make_salt()
    return make_pw_hash(pw, salt)

def make_cookie(username):
    salt = make_salt()
    return make_hash(username, salt)

class BaseHandler(webapp2.RequestHandler):

    def __init__(self, request, response):
        """
        overwrite init to set some variables for every request like user name
        """
        user_name_cookie = request.cookies.get("user_id")
        if user_name_cookie:
            self.user_id = check_cookie(user_name_cookie)

        #continue to init request and response
        self.initialize(request, response)

    def render(self, template_name, template_values):
        template = jinja_environment.get_template(template_name)
        self.response.out.write(template.render(template_values))

    def render_json(self, template_values):
        self.response.headers['Content-Type'] = "application/json; charset=UTF-8"
        self.response.out.write(json.dumps(template_values))
