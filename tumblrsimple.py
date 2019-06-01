#!/usr/bin/python

"""
TumblrSimple class for simplified tumblr operations over tumblr API

tumbkr API:     https://www.tumblr.com/docs/en/api/v2
web console:    https://api.tumblr.com/console/calls/blog/posts
tumblr apps:    https://www.tumblr.com/oauth/apps
pytumblr:       https://github.com/tumblr/pytumblr

"""

__VERSION__ = '2019.05.30'

import os, json
import re, datetime, time
import pytumblr


class TumblrSimple:
    """ simple Tumblr operations """

    verbosity = 0

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

    @classmethod
    def read_cfg(cls, filename):
        """ init tumbler from json config file """
        with open(filename, "r") as f:
            cfg = json.loads(f.read())
        cls.debug_json(3, "cfg:", cfg)
        return cls(cfg["consumer"], cfg["oauth"], cfg["blog_name"], cfg["options"]) if cfg else None

    @classmethod
    def no_warnings(cls):
        """ Suppress warnings: InsecurePlatformWarning, SNIMissingWarning """
        # https://stackoverflow.com/questions/29099404/ssl-insecureplatform-error-when-using-requests-package
        import requests.packages.urllib3
        requests.packages.urllib3.disable_warnings()

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

    def info_rq(self):
        """ get info """
        self.response = self.tumblr.info()
        self.debug_json(1, "tumblr.info()", self.response)
        return self.response_is_ok()

    def delete_post_rq(self, id):
        """ delete post id """
        self.response = self.tumblr.delete_post(self.blogname, id)
        self.debug_json(1, 'tumblr.delete_post(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def find_tag_rq(self, tag):
        """ find post id with tag tag """
        self.response =  self.tumblr.posts(self.blogname, tag=tag) if tag \
                    else self.tumblr.posts(self.blogname)
        self.debug_json(1, 'tumblr.posts(blogname=%s, tag=%s)' % (self.blogname, tag), self.response)
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

    def find_id_rq(self, id):
        """ get post for specific id """
        self.response = self.tumblr.posts(self.blogname, id=id)
        self.debug_json(1, 'tumblr.posts(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def get_path_from_response(self, path):
        """ get path from response via configurable path """
        # start from entire response
        result = self.response
        # iterate all parts in path
        for key in path.split('/'):
            # if key is plural take the first item from list
            result = result[key][0] if key.endswith('s') else result[key]
        return result

    def find_tag_get_ids(self, tag):
        """ get post ids [list]  with tag tag """
        if not self.find_tag_rq(tag=tag):
            return None
        return self.get_ids_from_response()

    def find_id_get_post(self, id, path='posts'):
        """ get post for specific id """
        if not self.find_id_rq(id=id):
            return None
        return self.get_path_from_response(path)

    def upload_photo_rq(self, photo, caption, tags):
        """ upload photo with caption and tags """
        # default timestamp is UTC now
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
        # rectify tags
        tags = self.rectify_tags(tags)
        # post photo
        self.response = self.tumblr.create_photo(
                            self.blogname, state="published", format="markdown",
                            tags=tags, data=photo,
                            caption=caption, date=gmtstr + ' GMT')
        self.debug_json(1, 'tumblr.create_photo(photo=%s, date=%s, tags=%s)' % (photo, gmtstr, tags), self.response)
        # check response for errors
        return self.response_is_ok()

    def upload_video_rq(self, video, caption, tags):
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
        # rectify tags
        tags = self.rectify_tags(tags)
        # post video
        self.response = self.tumblr.create_video(
                            self.blogname, state="published", format="markdown",
                            tags=tags, data=video,
                            caption=caption, date=gmtstr + ' GMT')
        self.debug_json(1, 'tumblr.create_video(video=%s, date=%s, tags=%s)' % (video, gmtstr, tags), self.response)
        # check response for errors
        return self.response_is_ok()

    def upload_photo_get_id_url(self, photo, caption, tags):
        """ upload photo with caption and tags and return id/url """
        # upload
        if not self.upload_photo_rq(photo, caption, tags):
            return None
        # get id
        id = self.get_id_from_response()
        # wait for server processing
        self.sleep(self.options.get("photo_wait", 5))
        # TODO: limit looping
        while not self.find_id_rq(id):
            self.sleep(self.options.get("photo_wait", 5))
        # get photo url
        url = self.get_path_from_response(path=self.options["photo_url"])
        #
        return {
            'id':   id,
            'url':  url
        }

    def upload_video_get_id_url(self, video, caption, tags):
        """ upload video with caption and tags and return id/url """
        # unique id (unix timestamp) to find uploaded post after server processing
        uid = datetime.datetime.now().strftime('%s')
        # upload with added uid tag
        if not self.upload_video_rq(video, caption, "%s,%s" % (tags, uid)):
            return None
        # this is just temporary/processing id returned from upload
        tid = self.get_id_from_response()
        # wait for server processing
        self.sleep(self.options.get("video_wait", 10))
        # sleep until temporary id is valid (server is processing video)
        # TODO: limit looping
        while self.find_id_rq(tid):
            self.sleep(self.options.get("video_wait", 10))
        # find post by uid
        if not self.find_tag_rq(uid):
            return None
        return {
            'id':  self.get_ids_from_response()[0],
            'url': self.get_path_from_response(path=self.options["video_url"])
        }

    def rectify_tags(self, tags, sep=',', trim=True, uniq=True, mapfnc=None, sortfnc=None):
        """ rectify (trim, unique, map, sort) tags (list or string) """
        # split string to list
        ltags = sep.split(tags) if type(tags) in [str, unicode] else tags
        if trim:
            ltags = map(str.strip, ltags)
        if uniq:
            ltags = list(set(ltags))
        if mapfnc:
            ltags = map(mapfnc, ltags)
        if sortfnc:
            ltags = sortfnc(ltags)
        # join list to string
        return sep.join(tags)

    @classmethod
    def debug_json(cls, level, action, jsn, stampfrm='[ %Y-%m-%d %X ]'):
        """ debug output with pretty formatted json """
        if level > cls.verbosity: return
        stamp = datetime.datetime.now().strftime(stampfrm) if stampfrm else ''
        print "%s" % stamp, '>>>', action, ">>>"
        print json.dumps(jsn, indent=4, sort_keys=True)
        print
