#!/usr/bin/python

__usage__ = """
usage: tumblr_cli_uploadr.py action file "caption" "tag1,tag2"

action ... photo, video, delete, find-tag
file
caption
tags
 
"""

import json
import os, sys, re, datetime
import pytumblr

# debug (verbosity) level
#
DBG = 0

# Suppress warnings: InsecurePlatformWarning, SNIMissingWarning
# https://stackoverflow.com/questions/29099404/ssl-insecureplatform-error-when-using-requests-package
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

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

def die_if_error(jsn):
    """ print error and die if there is an error in json """
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
    err = jsn.get("errors")
    if err:
        err = err[0]
        die("ERROR: %s - %s - %s" % (err["title"], err["code"], err["detail"]))


if __name__ == '__main__':

    # parameters
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

    # Authenticate via OAuth
    #
    client = pytumblr.TumblrRestClient(
        cfg["consumer"]["key"],
        cfg["consumer"]["secret"],
        cfg["oauth"]["token"],
        cfg["oauth"]["token_secret"]
    )

    info = client.info()
    debug_json(1, "client.info()", info)
    die_if_error(info)

    # DELETE id
    #
    if action in ['del', 'delete', 'rm', 'remove']:
        id = par
        result = client.delete_post(cfg["blog_name"], id)
        debug_json(1, 'delete result', result)
        die_if_error(result)

    # FIND-TAG tag
    #
    if action in ['find', 'find-tag']:
        result = client.posts(cfg["blog_name"], tag=par)
        debug_json(1, 'find tag', result)
        die_if_error(result)
        if result["posts"]:
            print "FOUND:",
            for post in result["posts"]:
                print post["id"],
            print
        else:
            print "NOT FOUND"

    # PHOTO file caption tags
    #
    if action in ["photo", "image", "picture"]:
        usage(required=4)
        photo, caption, tags = sys.argv[2], sys.argv[3], sys.argv[4]
        # basename
        basenamephoto = os.path.basename(photo)
        # default timestap is UTC now
        gmtstr = datetime.datetime.utcnow().isoformat(' ')
        # comma separated -> list, trim tags and skip empty tags
        tags = [ t.strip() for t in tags.split(',') if len(t.strip()) ]
        # optional add filename
        if cfg["auto_tag"]["filename"]:
            tags.append(basenamephoto)
        # optional add timestamp
        if cfg["auto_tag"]["timestamp"]:
            # FUJI20170721T134312.JPG
            m = re.match(r'[A-Za-z]+(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.[A-Za-z]+', basenamephoto)
            if m:
                y,m,d, hh,mm,ss = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)
                # "2019-01-10 22:26:25 GMT"
                gmtstr = "%s-%s-%s %s:%s:%s" % (y,m,d, hh,mm,ss)
                gmttag = "%s-%s-%sT%s:%s:%s" % (y, m, d, hh,mm,ss)
            else:
                # from file creation
                photomtime = os.path.getmtime(photo)
                # "2019-01-10 22:26:25 GMT"
                mtime = datetime.datetime.fromtimestamp(int(photomtime))
                gmtstr = mtime.isoformat(' ')
                gmttag = mtime.isoformat()
            tags.append(gmttag)
        # post photo
        result = client.create_photo(cfg["blog_name"], state="published", format="markdown",
                                    tags=tags, data=photo,
                                    caption=caption, date=gmtstr+' GMT')
        die_if_error(result)
        # id
        id = result["id"]
        # get available sizes
        url = client.posts(cfg["blog_name"], id=id)
        die_if_error(url)
        #
        for key in cfg["result"].split('/'):
            # if key is plural take the first item from list
            url = url[key][0] if key.endswith('s') else url[key]
        print "ID:", id
        print "URL:", url

    # VIDEO
    #

