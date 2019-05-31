#!/usr/bin/python

__VERSION__ = '2019.05.30'

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
%(exe)s find-tag tag            ... find post(s)   tagged with tag tag and print only id(s)
%(exe)s find-tag all            ... find all posts tagged with tag tag and print only ids
%(exe)s delete-id id            ... delete post id
%(exe)s delete-tagged tag       ... delete all post tagged with tag tag
%(exe)s photo file caption tags ... uploads photo file with caption and tags and print post id and url
%(exe)s video file caption tags ... uploads video file with caption and tags and print post id and url

""" % { 'about': __ABOUT__, 'exe': os.path.basename(sys.argv[0]), 'cfg': os.path.basename(sys.argv[0])[:-3] + '.json' }

# debug (verbosity) level
#
DBG = 0

import tumblrsimple


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


# =========
#   MAIN
# =========
#
if __name__ == '__main__':

    # parameters (min 2 required)
    #
    usage(required=2)
    action, par = sys.argv[1].lower(), sys.argv[2]

    # verbosity/debug level
    #
    tumblrsimple.TumblrSimple.verbosity = DBG

    # simple tumblr from cfg file
    #
    cfgfile = cfg_filename()
    tumblr = tumblrsimple.TumblrSimple.read_cfg(cfgfile)
    #
    if not tumblr:
        die("ERROR: broken config file: %s" % cfgfile)

    # suppress warnings: InsecurePlatformWarning, SNIMissingWarning for older libraries
    #
    tumblr.no_warnings()

    # validate authorization
    #
    if not tumblr.info_rq():
        die(tumblr.last_error())

    # DELETE id
    #
    if action in ['del-id', 'delete-id', 'rm-id', 'remove-id']:
        id = None if par in ['*', 'all', '-'] else par
        if not tumblr.delete_post_rq(id=id):
            die(tumblr.last_error())

    # DELETE tagged
    #
    if action in ['del-tagged', 'delete-tagged', 'rm-tagged', 'remove-tagged']:
        ids = tumblr.find_tag_get_ids(tag=par)
        if not ids:
            die(tumblr.last_error())
        for id in ids:
            if not tumblr.delete_post_rq(id=id):
                die(tumblr.last_error())

    # FIND-TAG tag
    #
    if action in ['find', 'find-tag', 'tag']:
        tag = None if par in ['*', 'all', '-'] else par
        ids = tumblr.find_tag_get_ids(tag=tag)
        if not ids:
            die(tumblr.last_error())
        print "ID:", ' '.join(["%s" % id for id in ids])

    # FIND-ID id
    #
    if action in ['id', 'find-id']:
        post = tumblr.find_id_get_post(id=par)
        if not post:
            die(tumblr.last_error())
        tumblr.debug_json(0, "post[%s]" % par, post)

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
        print "ID:",  idurl['id']
        print "URL:", idurl['url']

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
        print "ID:",  idurl['id']
        print "URL:", idurl['url']
