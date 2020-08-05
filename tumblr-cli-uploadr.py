#!/usr/bin/python3

__VERSION__ = '2020.08.04'

__ABOUT__   = '= tubmlr - command line uploader = (c) 2019 by Robert = version %s =' % __VERSION__

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
%(exe)s find-tag tag            ... find post(s)   tagged with tag tag and print only post id(s)
%(exe)s list-tag id             ... list all tags for post id
%(exe)s list-tag all            ... list all tags for all posts (all = * = -)
%(exe)s list-posts              ... list all posts (print only post id(s))
%(exe)s delete-id id            ... delete post id
%(exe)s delete-id all           ... delete all posts (all = * = -)
%(exe)s delete-tagged tag       ... delete all post tagged with tag tag
%(exe)s add-tag tag1,tag2 id    ... add tag1 and tag2 to post id
%(exe)s del-tag tag1,tag2 id    ... delete tag1 and tag2 from post id
%(exe)s photo file caption tags ... uploads photo file with caption and tags and print post id and url
%(exe)s video file caption tags ... uploads video file with caption and tags and print post id and url
""" % { 'about': __ABOUT__, 'exe': os.path.basename(sys.argv[0]), 'cfg': os.path.basename(sys.argv[0]).replace('.py', '.json') }

# debug (verbosity) level
#
DBG = 0

import tumblrsimple


def die(msg, exitcode=1):
    """ print msg and die with exitcode """
    print(msg)
    sys.exit(exitcode)

def usage(required=4):
    """ show usage if not enough parameters supplied """
    # just return if we have all required parameters
    if len(sys.argv) > required:
        return
    # show usage help and die
    die(__usage__)


# =========
#   MAIN
# =========
#
if __name__ == '__main__':

    # parameters (min 1 required)
    #
    usage(required=1)
    action = sys.argv[1].lower()

    # verbosity/debug level
    #
    tumblrsimple.TumblrSimple.verbosity = DBG

    # simple tumblr from cfg file
    #
    cfgfile = tumblrsimple.TumblrSimple.cfg_filename(sys.argv[0])
    tumblr = tumblrsimple.TumblrSimple.read_cfg(cfgfile)
    #
    if not tumblr:
        die("ERROR: broken/missing config file: %s" % cfgfile)

    # suppress warnings: InsecurePlatformWarning, SNIMissingWarning for older libraries
    #
    #tumblr.no_warnings()

    # validate authorization
    #
    if not tumblr.info_rq():
        die(tumblr.last_error())

    # LIST-POSTS
    #
    if action in ['list-posts', 'list-id']:
        ids = tumblr.list_posts_ids()
        if not ids:
            die(tumblr.last_error())
        print("IDs:", ' '.join(["%s" % id for id in ids]))

    # LIST-TAG id
    #
    if action in ['list-tag', 'list-tags']:
        usage(required=2)
        id = sys.argv[2]
        if id in ['*', 'all', '-']:
            id_tags = tumblr.list_posts_tags()
            if not id_tags:
                die(tumblr.last_error())
            for id,tags in id_tags.items():
                print("ID:", id, end=' ')
                print("TAGs:", ' '.join(["%s" % tag for tag in tags]))
        else:
            tags = tumblr.find_id_get_tags(id=id)
            if not tags:
                die(tumblr.last_error())
            print("ID:", id, end=' ')
            print("TAGs:", ' '.join(["%s" % tag for tag in tags]))

    # DELETE id
    #
    if action in ['del-id', 'delete-id', 'rm-id', 'remove-id']:
        usage(required=2)
        par = sys.argv[2]
        id = None if par in ['*', 'all', '-'] else par
        if not tumblr.delete_post_rq(id=id):
            die(tumblr.last_error())
        print("DELETED ID:", id)

    # DELETE tagged
    #
    if action in ['del-tagged', 'delete-tagged', 'rm-tagged', 'remove-tagged']:
        usage(required=2)
        par = sys.argv[2]
        ids = tumblr.find_tag_get_ids(tag=par)
        if not ids:
            die(tumblr.last_error())
        for id in ids:
            if not tumblr.delete_post_rq(id=id):
                die(tumblr.last_error())
        print("DELETED IDs:", ' '.join(["%s" % id for id in ids]))

    # FIND-TAG tag
    #
    if action in ['find', 'find-tag', 'tag']:
        usage(required=2)
        par = sys.argv[2]
        tag = None if par in ['*', 'all', '-'] else par
        ids = tumblr.find_tag_get_ids(tag=tag)
        print("TAG: #%s" % tag)
        if not ids:
            die(tumblr.last_error())
        print("IDs:", ' '.join(["%s" % id for id in ids]))

    # FIND-ID id
    #
    if action in ['id', 'find-id']:
        usage(required=2)
        id = sys.argv[2]
        post = tumblr.find_id_get_post(id=id)
        if not post:
            die(tumblr.last_error())
        tumblr.debug_json(0, "post[%s]" % id, post)

    # ADD-TAG tag1,tag2 id
    #
    if action in ['add-tag', 'add-tags']:
        usage(required=3)
        tags = sys.argv[2]
        id   = sys.argv[3]
        post = tumblr.id_add_tags(id=id, addtags=tags)
        if not post:
            die(tumblr.last_error())
        print("ID:",id,"+TAGS:",tags)

    # DEL-TAG tag1,tag2 id
    #
    if action in ['del-tag', 'del-tags', 'rm-tag', 'rm-tags']:
        usage(required=3)
        tags = sys.argv[2]
        id   = sys.argv[3]
        post = tumblr.id_del_tags(id=id, deltags=tags)
        if not post:
            die(tumblr.last_error())
        print("ID:", id, "-TAGS:", tags)

    # PHOTO file caption tags
    #
    if action in ["photo", "image", "picture"]:
        # 4 pars required
        usage(required=4)
        photo, caption, tags = sys.argv[2], sys.argv[3], sys.argv[4]
        # upload
        idurl = tumblr.upload_photo_get_id_url(photo, caption, tags)
        if not idurl:
            die(tumblr.last_error())
        #
        print("PHOTO:", photo)
        print("CAPTION:", caption)
        print("TAGs:", tags)
        print("ID:",  idurl['id'])
        print("URL:", idurl['url'])

    # VIDEO
    #
    if action in ["video", "vid", "avi", "mp4"]:
        # 4 pars required
        usage(required=4)
        video, caption, tags = sys.argv[2], sys.argv[3], sys.argv[4]
        # upload
        idurl = tumblr.upload_video_get_id_url(video, caption, tags)
        if not idurl:
            die(tumblr.last_error())
        #
        print("VIDEO:", video)
        print("CAPTION:", caption)
        print("TAGs:", tags)
        print("ID:",  idurl['id'])
        print("URL:", idurl['url'])

    # API calls stats
    #
    print("Done - Tumblr.API calls:", tumblr.api_rq_cnt)
