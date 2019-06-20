#!/usr/bin/python

"""
TumblrSimple class for simplified tumblr operations over tumblr API

tumbkr API:     https://www.tumblr.com/docs/en/api/v2
web console:    https://api.tumblr.com/console/calls/blog/posts
tumblr apps:    https://www.tumblr.com/oauth/apps
pytumblr:       https://github.com/tumblr/pytumblr

"""

__VERSION__ = '2019.06.18'

import os, json
import re, datetime, time
import pytumblr


class Tags:
    """ tags class for working with tags as csv string and tags as list """

    # separator / csv string format
    sep = ','

    # preprocess each item before processing
    rectify_item = unicode.strip

    def __init__(self, data):
        """ init from string or list """
        # create unicode list from string/unicode
        if type(data) != list:
            data = [ unicode(t, 'utf8') if type(t) == str else t for t in data.split(Tags.sep) ]
        # rectify list items
        self.lst = map(Tags.rectify_item, data)

    def as_string(self):
        return self.sep.join(self.lst)

    def as_list(self):
        return self.lst

    def remove(self, data):
        if type(data) == list:
            for item in data:
                item = Tags.rectify_item(item)
                if item in self.lst:
                    self.lst.remove(item)
        else:
            # force unicode
            if type(data) == str:
                data = unicode(data, 'utf8')
            # only remove if present in the list
            if data in self.lst:
                self.lst.remove(Tags.rectify_item(data))
        return self

    def add(self, data):
        if type(data) == list:
            for item in data:
                item = Tags.rectify_item(item)
                if item not in self.lst:
                    self.lst.append(item)
        else:
            # force unicode
            if type(data) == str:
                data = unicode(data, 'utf8')
            # only add tag if not already in the list
            if data not in self.lst:
                self.lst.append(Tags.rectify_item(data))
        return self


class TumblrSimple:
    """ simple Tumblr operations """

    verbosity = 0

    api_rq_cnt = 0

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
    def no_warnings(cls):
        """ Suppress warnings: InsecurePlatformWarning, SNIMissingWarning """
        # https://stackoverflow.com/questions/29099404/ssl-insecureplatform-error-when-using-requests-package
        import requests.packages.urllib3
        requests.packages.urllib3.disable_warnings()

    @classmethod
    def read_cfg(cls, filename):
        """ init tumbler from json config file, returns None if any error occured """
        try:
            with open(filename, "r") as f:
                cfg = json.loads(f.read())
            cls.debug_json(3, "cfg:", cfg)
        except IOError:
            cfg = None
        return cls(cfg["consumer"], cfg["oauth"], cfg["blog_name"], cfg["options"]) if cfg else None

    @classmethod
    def cfg_filename(cls, exename, ext='.json'):
        """ derive cfg filename from exename and add extension ext """
        basename = os.path.basename(exename)
        # replace extension
        return basename.replace('.py', ext) if basename.endswith('.py') else basename + ext

    @classmethod
    def debug_json(cls, level, action, jsn, stampfrm='[ %Y-%m-%d %X ]'):
        """ debug output with pretty formatted json """
        if level > cls.verbosity: return
        stamp = datetime.datetime.now().strftime(stampfrm) if stampfrm else ''
        print "%s" % stamp, '>>>', action, ">>>"
        print json.dumps(jsn, indent=4, sort_keys=True)
        print

    # helpers - consider them to be static or class methods

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

    def sleep(self, sec):
        """ sleep sec seconds """
        time.sleep(sec)
        return

    # tumblr requests

    def info_rq(self):
        """ get info """
        self.response = self.tumblr.info()
        self.api_rq_cnt += 1
        self.debug_json(1, "tumblr.info()", self.response)
        return self.response_is_ok()

    def delete_post_rq(self, id):
        """ delete post id """
        self.response = self.tumblr.delete_post(self.blogname, id)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.delete_post(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def edit_post_rq(self, id, **kwargs):
        """ edit post id """
        self.response = self.tumblr.edit_post(self.blogname, id=id, **kwargs)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.edit_post(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def posts_rq(self):
        """ get all posts """
        self.response = self.tumblr.posts(self.blogname)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.posts(blogname=%s)' % (self.blogname), self.response)
        return self.response_is_ok()

    def find_id_rq(self, id):
        """ get post for specific id """
        self.response = self.tumblr.posts(self.blogname, id=id)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.posts(blogname=%s, id=%s)' % (self.blogname, id), self.response)
        return self.response_is_ok()

    def find_tag_rq(self, tag):
        """ find post id with tag tag """
        self.response =  self.tumblr.posts(self.blogname, tag=tag)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.posts(blogname=%s, tag=%s)' % (self.blogname, tag), self.response)
        return self.response_is_ok()

    def upload_photo_rq(self, photo, caption, csvtags):
        """ upload photo with caption and tags """
        # default timestamp is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tg = Tags(csvtags)
        # optional add filename
        if self.options.get("auto_tag_filename"):
            tg.add(os.path.basename(photo))
        # optional add timestamp
        if self.options.get("auto_tag_timestamp"):
            gmt = self.gmt_media(photo)
            tg.add(gmt)
            gmtstr = gmt.replace('T', ' ')
        # tags in csv format as string
        ltags = tg.as_list()
        # post photo
        self.response = self.tumblr.create_photo(
            self.blogname, state="published", format="markdown",
            tags=ltags, data=photo,
            caption=caption, date=gmtstr + ' GMT')
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.create_photo(photo=%s, date=%s, tags=%s)' % (photo, gmtstr, ltags), self.response)
        # check response for errors
        return self.response_is_ok()

    def upload_video_rq(self, video, caption, csvtags):
        """ upload video with caption and tags """
        # default timestap is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tg = Tags(csvtags)
        # optional add filename
        if self.options.get("auto_tag_filename"):
            tg.add(os.path.basename(video))
        # optional add timestamp
        if self.options.get("auto_tag_timestamp"):
            gmt = self.gmt_media(video)
            tg.add(gmt)
            gmtstr = gmt.replace('T', ' ')
        # tags in csv format as string
        ltags = tg.as_list()
        # post video
        self.response = self.tumblr.create_video(
            self.blogname, state="published", format="markdown",
            tags=ltags, data=video,
            caption=caption, date=gmtstr + ' GMT')
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.create_video(video=%s, date=%s, tags=%s)' % (video, gmtstr, ltags), self.response)
        # check response for errors
        return self.response_is_ok()

    # response processing

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

    def get_ids_from_response(self):
        """ get list of ids from last response """
        ids = [post.get("id") for post in self.response["posts"]]
        return ids

    def get_tags_from_response(self):
        """ get dict of id -> [tags] from last response """
        tags = dict([ (post.get("id"), post.get("tags")) for post in self.response["posts"]])
        return tags

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

    def get_xpath_from_response(self, xpath):
        """ get simplified xpath from response """
        # start from entire response
        result = self.response
        self.debug_json(7, 'TumblrSimple.get_xpath_from_response(%s) result:' % xpath, result)
        # iterate all parts in xpath
        for key in xpath.strip('/').split('/'):
            # list[x] ?
            m = re.match(r'^(\w+)\[(.+)\]$', key)
            self.debug_json(7, 'TumblrSimple.get_xpath_from_response() key(%s) m(%s) result:' % (key, m.groups() if m else 'None'), result)
            if m:
                wkey, idx = m.group(1), int(m.group(2)) if m.group(2).isdigit() else m.group(2)
                arr = result[wkey]
                result = arr if idx == '' else arr[idx]
            else:
                result = result[key]
        return result

    # tumblrsimple methods to be called

    def list_posts_ids(self):
        """ list all posts id(s) """
        if not self.posts_rq():
            return None
        return self.get_ids_from_response()

    def list_posts_tags(self):
        """ list all posts id(s) """
        if not self.posts_rq():
            return None
        return self.get_tags_from_response()

    def find_tag_get_ids(self, tag):
        """ get post ids [list]  with tag tag """
        if not self.find_tag_rq(tag=tag):
            return None
        return self.get_ids_from_response()

    def find_id_get_xpath(self, id, xpath):
        """ get xpath for specific id """
        if not self.find_id_rq(id=id):
            return None
        return self.get_xpath_from_response(xpath)

    def find_id_get_post(self, id):
        """ get post for specific id """
        return self.find_id_get_xpath(id, xpath='/posts[0]')

    def find_id_get_tags(self, id):
        """ get post for specific id """
        return self.find_id_get_xpath(id, xpath='/posts[0]/tags')

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
        url = self.get_xpath_from_response(xpath=self.options["photo_url"])
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
        # result id/url
        id_url = {
            'id':  self.get_ids_from_response()[0],
            'url': self.get_xpath_from_response(xpath=self.options["video_url"])
        }
        # remove uid tag
        self.id_del_tags(id=id_url['id'], deltags="%s" % uid)
        #
        return id_url

    def id_add_tags(self, id, addtags):
        """ add tags (csv or list) to post id """
        # post-id tags
        tgs = Tags(self.find_id_get_tags(id=id))
        # add new tags
        tgs.add(addtags)
        # edit post with new tags
        return self.edit_post_rq(id, tags=tgs.as_list())

    def id_del_tags(self, id, deltags):
        """ remove tags (csv or list) from post id """
        # post-id tags
        tgs = Tags(self.find_id_get_tags(id=id))
        # remove tags
        tgs.remove(deltags)
        # edit post with new tags
        return self.edit_post_rq(id, tags=tgs.as_list())
