import hashlib

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

    logging.info("user_id: %s, hash_value: %s, salt: %s" %(user_id,hash_value,salt))
    if make_hash(user_id, salt) == cookie_string:
        return user_id
    else:
        return None

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_hash(user_id, salt):
    h = hashlib.sha256(salt + user_id + salt).hexdigest()
    return "%s|%s|%s" % (user_id,h,salt)

def make_pw_hash(pw, salt):
    h = hashlib.sha256(pw + salt).hexdigest()
    return "%s|%s" % (h,salt)