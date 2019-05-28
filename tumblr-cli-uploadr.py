#!/usr/bin/python

__VERSION__ = '2019.05.15'

__ABOUT__   = '= tubmlr - command line uploader = ver %s = (c) 2019 by Robert =' % __VERSION__

import os, sys

__usage__ = """
%(about)s

usage: %(exe)s action file "caption" "tag1,tag2"

action  ... photo, video, delete, find-tag, find-id
file    ... media file to upload
caption ... markdown formatted text for caption
tags    ... comma separated values for tags

for configurable options check config file: %(cfg)s
 
example:
%(exe)s find-id id              ... find post id and print full json
%(exe)s find-id all             ... find all posts and print full json
%(exe)s find-tag tag            ... find post(s) with tag tag and print only id(s)
%(exe)s find-tag all            ... find all posts with tag tag and print only ids
%(exe)s delete id               ... delete post id
%(exe)s photo file caption tags ... uploads photo file with caption and tags and print post id and url
%(exe)s video file caption tags ... uploads video file with caption and tags and print post id and url

""" % { 'about': __ABOUT__, 'exe': os.path.basename(sys.argv[0]), 'cfg': os.path.basename(sys.argv[0])[:-3] + '.json' }

# debug (verbosity) level
#
DBG = 10

import json
import re, datetime, time
import pytumblr

# Suppress warnings: InsecurePlatformWarning, SNIMissingWarning
# https://stackoverflow.com/questions/29099404/ssl-insecureplatform-error-when-using-requests-package
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

class TumblrSimple:
    """ simple Tumblr operations """

    def __init__(self, consumer, oauth, blogname, options):
        """ init tumblr with auth parameters, blogname and options """
        self.tumblr = pytumblr.TumblrRestClient(
            consumer["key"],
            consumer["secret"],
            oauth["token"],
            oauth["token_secret"]
        )
        self.blogname = blogname
        self.options  = options

    def sleep(self, sec):
        """ sleep sec seconds """
        time.sleep(sec)
        return

    def last_error(self, idx=0):
        """ build error message from last response
        #    "errors": [
        #        {
        #            "code": 1016,
        #            "detail": "Unable to authorize",
        #            "title": "Unauthorized"
        #        }
        #    ],
        #    "meta": {
        #        "msg": "Unauthorized",
        #        "status": 401
        #    }

        #    "meta": {
        #        "msg": "Bad Request",
        #        "status": 400
        #    },
        #    "response": {
        #        "errors": [
        #            "Nice image, but we don't support that format. Try resaving it as a gif, jpg, or png."
        #        ]
        #    }

        """
        if self.response_is_ok():
            return
        if self.response.get("errors"):
            err = self.response["errors"][idx]
            msg = "ERROR: %s - %s - %s" % (err["title"], err["code"], err["detail"])
            return msg
        if self.response.get("response"):
            msg = self.response["response"]["errors"]
            return msg
        return "unknown error ?! check json response"

    def response_is_ok(self):
        """ check if response does not contain errors """
        meta = self.response.get("meta")
        return False if meta else True

    def info(self):
        """ get info """
        self.response = self.tumblr.info()
        debug_json(1, "tumblr.info()", self.response)
        return self.response_is_ok()

    def delete_post(self, id):
        """ delete post id """
        self.response = self.tumblr.delete_post(self.blogname, id)
        debug_json(1, 'tumblr.delete_post(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def find_tag(self, tag):
        """ find post id with tag tag """
        self.response =  self.tumblr.posts(self.blogname, tag=tag) if tag \
                    else self.tumblr.posts(self.blogname)
        debug_json(1, 'tumblr.posts(tag=%s)' % tag, self.response)
        return self.response_is_ok()

    def get_ids_from_response(self):
        """ get list of ids from last response """
        ids = [ post.get("id") for post in self.response["posts"] ]
        return ids

    def get_id_from_response(self):
        """ get is from response """
        return self.response.get("id")

    def get_blogs_from_response(self):
        """ get list of blogs from info response """
        user = self.response.get("user")
        return user.get("blogs", []) if user else []

    def get_post_format_from_response(self):
        """ get default post format (markdown, html) """
        user = self.response.get("user")
        return user.get("default_post_format", '?') if user else '?'

    def trim_tags(self, tags):
        """ trim tags and covert from comma separated values to list """
        return [t.strip() for t in tags.split(',') if len(t.strip())]

    def gmt_media(self, media):
        """ get GMT time from media filename or file in isoformat YYYY-MM-DDTHH:mm:ss """
        # basename
        basenamemedia = os.path.basename(media)
        # default gmt from media file
        mtime = datetime.datetime.fromtimestamp(int(os.path.getmtime(media)))
        gmt = mtime.isoformat()
        # try media file name FUJI20170721T134312.JPG
        m = re.match(r'[A-Za-z]+(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.[A-Za-z]+', basenamemedia)
        if m:
            y, m, d, hh, mm, ss = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
            # "2019-01-10T22:26:25"
            gmt = "%s-%s-%sT%s:%s:%s" % (y, m, d, hh, mm, ss)
        return gmt

    def find_id(self, id):
        """ get post for specific id """
        self.response = self.tumblr.posts(self.blogname, id=id)
        debug_json(1, 'tumblr.posts(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def get_url_from_response(self, path):
        """ get url from response via configurable path """
        # start from entire response
        url = self.response
        for key in path.split('/'):
            # if key is plural take the first item from list
            url = url[key][0] if key.endswith('s') else url[key]
        return url

    def upload_photo(self, photo, caption, tags):
        """ upload photo with caption and tags """
        # default timestap is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tags = self.trim_tags(tags)
        # optional add filename
        if self.options.get("auto_tag_filename"):
            tags.append(os.path.basename(photo))
        # optional add timestamp
        if self.options.get("auto_tag_timestamp"):
            gmt = self.gmt_media(photo)
            tags.append(gmt)
            gmtstr = gmt.replace('T', ' ')
        # post photo
        self.response = self.tumblr.create_photo(
                            self.blogname, state="published", format="markdown",
                            tags=tags, data=photo,
                            caption=caption, date=gmtstr + ' GMT')
        debug_json(1, 'tumblr.create_photo(photo=%s, date=%s, tags=%s)' % (photo, gmtstr, tags), self.response)
        # check response for errors
        return self.response_is_ok()

    def upload_video(self, video, caption, tags):
        """ upload video with caption and tags """
        # default timestap is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tags = self.trim_tags(tags)
        # optional add filename
        if self.options.get("auto_tag_filename"):
            tags.append(os.path.basename(video))
        # optional add timestamp
        if self.options.get("auto_tag_timestamp"):
            gmt = self.gmt_media(video)
            tags.append(gmt)
            gmtstr = gmt.replace('T', ' ')
        # post video
        self.response = self.tumblr.create_video(
                            self.blogname, state="published", format="markdown",
                            tags=tags, data=video,
                            caption=caption, date=gmtstr + ' GMT')
        debug_json(1, 'tumblr.create_video(video=%s, date=%s, tags=%s)' % (video, gmtstr, tags), self.response)
        # check response for errors
        return self.response_is_ok()


def die(msg, exitcode=1):
    """ print msg and die woth exitcode """
    print msg
    sys.exit(exitcode)

def usage(required=4):
    """ show usage if not enough parameters supplied """
    # just return if we have all required parameters
    if len(sys.argv) > required:
        return
    # show usage help and die
    die(__usage__)

def cfg_filename(ext='.json'):
    """ derive cfg filename from argv[0] and add extension ext """
    basename = os.path.basename(sys.argv[0])
    # remove '.py' extension
    if basename.endswith('.py'):
        basename = basename[:-3]
    # add extension
    return basename + ext

def read_cfg(filename):
    """ read cfg from local json file basename.json """
    # read json
    with open(filename, "r") as f:
        cfgdata = json.loads(f.read())
    return cfgdata

def debug_json(level, action, jsn):
    """ debug output with pretty formatted json """
    if level > DBG: return
    print ">>>",action,">>>"
    print json.dumps(jsn, indent=4, sort_keys=True)
    print


# =========
#   MAIN
# =========
#
if __name__ == '__main__':

    # parameters (min 2 required)
    #
    usage(required=2)
    action, par = sys.argv[1].lower(), sys.argv[2]

    # CFG
    #
    cfgfile = cfg_filename()
    cfg = read_cfg(cfgfile)
    debug_json(3, "cfg:", cfg)

    if not cfg:
        die("ERROR: broken config file: %s" % cfgfile)

    # simple tumblr
    #
    tumblr = TumblrSimple(cfg["consumer"], cfg["oauth"], cfg["blog_name"], cfg["options"])

    # validate authorization
    #
    if not tumblr.info():
        die(tumblr.last_error())

    #
    blogs = tumblr.get_blogs_from_response()
    print "BLOGS:",blogs
    format = tumblr.get_post_format_from_response()
    print "FORMAT:",format

    # DELETE id
    #
    if action in ['del', 'delete', 'rm', 'remove']:
        id = None if par in ['*', 'all', '-'] else par
        if not tumblr.delete_post(id=id):
            die(tumblr.last_error())

    # FIND-TAG tag
    #
    if action in ['find', 'find-tag', 'tag']:
        tag = None if par in ['*', 'all', '-'] else par
        if not tumblr.find_tag(tag=tag):
            die(tumblr.last_error())
        print "ID:", ' '.join(["%s" % id for id in tumblr.get_ids_from_response()])

    # FIND-ID id
    #
    if action in ['id', 'find-id']:
        if not tumblr.find_id(id=par):
            die(tumblr.last_error())
        debug_json(0, "tumblr.find_id(%s)" % par, tumblr.response)

    # PHOTO file caption tags
    #
    if action in ["photo", "image", "picture"]:
        # 4 pars required
        usage(required=4)
        photo, caption, tags = sys.argv[2], sys.argv[3], sys.argv[4]
        # upload
        if not tumblr.upload_photo(photo, caption, tags):
            die(tumblr.last_error())
        id = tumblr.get_id_from_response()
        # wait for server processing
        tumblr.sleep(tumblr.options.get("photo_wait", 5))
        # find post by id
        if not tumblr.find_id(id):
            die(tumblr.last_error())
        url = tumblr.get_url_from_response(tumblr.options["photo_url"])
        #
        print "ID:", id
        print "URL:", url

    # VIDEO
    #
    if action in ["video", "vid", "avi", "mp4"]:
        # 4 pars required
        usage(required=4)
        video, caption, tags = sys.argv[2], sys.argv[3], sys.argv[4]
        # upload
        if not tumblr.upload_video(video, caption, tags):
            die(tumblr.last_error())
        # this is just temporary/processing id
        id = tumblr.get_id_from_response()
        # wait for server processing
        tumblr.sleep(tumblr.options.get("video_wait", 10))
        # sleep until temporary id is valid
        while tumblr.find_id(id):
            tumblr.sleep(tumblr.options.get("video_wait", 10))
        # find post by filename tag
        tag = os.path.basename(video)
        if not tumblr.find_tag(tag):
            die(tumblr.last_error())
        url = tumblr.get_url_from_response(tumblr.options["video_url"])
        id  = tumblr.get_ids_from_response()[0]
        #
        print "ID:", id
        print "URL:", url
