#!/usr/bin/python

"""
TumblrSimple class for simplified tumblr operations over tumblr API

tumbkr API:     https://www.tumblr.com/docs/en/api/v2
web console:    https://api.tumblr.com/console/calls/blog/posts
tumblr apps:    https://www.tumblr.com/oauth/apps
pytumblr:       https://github.com/tumblr/pytumblr

"""

__VERSION__ = '2019.06.20'

import os, json
import re, datetime, time
import pytumblr

# Max 20 Tags -  https://unwrapping.tumblr.com/tagged/tumblr-limits

class Tags:
    """ tags class for working with tags as csv string and tags as list """

    def __init__(self, data=None, sep=','):
        """ init from optional data (string or list or csv)"""
        # store csv separator
        self.sep = sep
        # rectify and convert to list
        self.lst = self._to_relist(data) if data else []

    def _rectify_item(self, item):
        """ preprocess single item """
        # force unicode
        item = unicode(item, 'utf8') if type(item) == str else item
        # stip whitespaces, strip seprators, covert to lowrcase
        return item.strip().strip(self.sep).lower()

    def _to_relist(self, par):
        """ convert par to rectified list """
        # assume csv if separator found in par
        par = par.split(self.sep) if self.sep in par else par
        # convert to list even if single item
        par = par if type(par) == list else [par]
        # rectify and return
        return map(self._rectify_item, par)

    def as_string(self):
        return self.sep.join(self.lst)

    def as_list(self):
        return self.lst

    def _remove1(self, item):
        """ remove single item """
        # remove
        if item in self.lst:
            self.lst.remove(item)
        return self

    def remove(self, data):
        """ remove list or item or csv """
        for item in self._to_relist(data):
            self._remove1(item)
        #
        return self

    def _add1(self, item, pos=None):
        """ add single item at optional position pos - append by default """
        # avoid duplicitiy
        if item not in self.lst:
            # insert or append
            self.lst.append(item) if pos is None else self.lst.insert(pos, item)
        #
        return self

    def add(self, data, pos=None):
        """ add list or item or csv at optional pos - append by default """
        for item in self._to_relist(data):
            self._add1(item, pos)
        #
        return self

    def limit_len(self, minlen=5):
        """ elmininate tags shorter than minlen """
        self.lst = filter(lambda tag: len(tag) >= minlen, self.lst)
        return self

    def limit_num(self, maxnum=20):
        """ limit number of tags by removing shortest ones """
        # start eliminating the shortest tag
        for tag in sorted(self.lst, key=len):
            # we are done when number <= maxnum
            if len(self.lst) <= maxnum: break
            # remove shortest tag
            self.lst.remove(tag)
        #
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

    def upload_photo_rq(self, photo, caption, csvtags, **kwargs):
        """ upload photo with caption and tags """
        #:param slug: a string, a short text summary to the end of the post url
        #:param link: a string, the 'click-through' url you want on the photo
        #:param source: a string, the photo source url
        #
        # default timestamp is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tg = Tags(csvtags)
        # optional add filename at the begining
        if self.options.get("auto_tag_filename"):
            tg.add(os.path.basename(photo), pos=0)
        # gmt from filename or file
        gmt = self.gmt_media(photo)
        gmtstr = gmt.replace('T', ' ')
        # optional add timestamp after the filename
        if self.options.get("auto_tag_timestamp"):
            tg.add(gmt.replace('T', '-'), pos=1)
        # elmiminate shorter tags, limit number of tags and get in csv format as string
        ltags = tg.limit_len(minlen=5).limit_num(maxnum=20).as_list()
        # post photo
        self.response = self.tumblr.create_photo(
            self.blogname, state="published", format="markdown",
            tags=ltags, data=photo,
            caption=caption, date=gmtstr + ' GMT',
            **kwargs)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.create_photo(photo=%s, date=%s, tags=%s, kwargs=%s)' \
                        % (photo, gmtstr, ltags, kwargs), self.response)
        # check response for errors
        return self.response_is_ok()

    def upload_video_rq(self, video, caption, csvtags, **kwargs):
        """ upload video with caption and tags """
        #:param slug: a string, a short text summary to the end of the post url
        #:param embed: a string, the emebed code that you'd like to upload
        #
        # default timestap is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tg = Tags(csvtags)
        # optional add filename after uid
        if self.options.get("auto_tag_filename"):
            tg.add(os.path.basename(video), pos=1)
        # gmt from filename or file
        gmt = self.gmt_media(video)
        gmtstr = gmt.replace('T', ' ')
        # optional add timestamp after uid,filename
        if self.options.get("auto_tag_timestamp"):
            tg.add(gmt.replace('T', '-'), pos=2)
        # elmiminate shorter tags, limit number of tags and get in csv format as string
        ltags = tg.limit_len(minlen=5).limit_num(maxnum=20).as_list()
        # post video
        self.response = self.tumblr.create_video(
            self.blogname, state="published", format="markdown",
            tags=ltags, data=video,
            caption=caption, date=gmtstr + ' GMT',
            **kwargs)
        self.api_rq_cnt += 1
        self.debug_json(1, 'tumblr.create_video(video=%s, date=%s, tags=%s, kwargs=%s)' \
                        % (video, gmtstr, ltags, kwargs), self.response)
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

    def upload_photo_get_id_url(self, photo, caption, tags, **kwargs):
        """ upload photo with caption and tags and return id/url """
        # upload
        if not self.upload_photo_rq(photo, caption, tags, **kwargs):
            return None
        # get id
        id = self.get_id_from_response()
        # wait for server processing
        for i in range(self.options.get("loop_wait", 100)):
            self.sleep(self.options.get("photo_wait", 5))
            # success if id found
            if self.find_id_rq(id): break
        # timeout waiting for server processing
        else:
            return None
        # get photo url
        url = self.get_xpath_from_response(xpath=self.options["photo_url"])
        #
        return {
            'id':   id,
            'url':  url
        }

    def upload_video_get_id_url(self, video, caption, tags, **kwargs):
        """ upload video with caption and tags and return id/url """
        # unique id (unix timestamp) to find uploaded post after server processing
        uid = datetime.datetime.now().strftime('%s')
        # upload with added uid tag
        if not self.upload_video_rq(video, caption, "%s,%s" % (uid, tags), **kwargs):
            return None
        # this is just temporary/processing id returned from upload
        tid = self.get_id_from_response()
        # wait for server processing
        for i in range(self.options.get("loop_wait", 100)):
            self.sleep(self.options.get("video_wait", 10))
            # success if temporary tid not found any more - processing done
            if not self.find_id_rq(tid): break
        # timeout waiting for server processing
        else:
            return None
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
