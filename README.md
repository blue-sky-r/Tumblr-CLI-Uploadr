## Tumblr-CLI-Uploadr

Command line (CLI) Tumblr uploader written in python (python3 compatible).

It provides simplistic command line interface CLI for tumblrsimple.py

Supports basic [tumblr](https://www.tumblr.com/docs/en/api/v2) operations:

* photo/video media: upload, find, delete
* media tag: list, find, add, remove


    Note: follow, likes and dashboard related functionality is intentionally not implemented


#### requirements

For fully functional CLI clients all following components are required:

* [PyTumblr](https://github.com/tumblr/pytumblr) tumblr API class
    
* [TumblrSimple](#tumblrsimple) wrapper class for PyTumblr

* [tumblr-cli-uploadr](#tumblr-cli-uploadr-1) CLI client 

* [tumblr-cli-uploadr.json](#tumblr-cli-uploadrjson) JSON config


#### PyTumblr

PyTumblr is python class fot API calls provided officially by [tumblr on GitHub](https://github.com/tumblr/pytumblr).

Use pip for installation:

    pip3 install PyTumblr


#### TumblrSimple

Class Tags handles tag related processing while exposing result either as_string() or as_list().
  
TumblrSimple is wrapper for PyTumblr to provide more user friendly methods to tumblr API:

    list_posts_ids()
    find_id_get_post(id)
    find_tag_get_ids(tag)
    
    upload_photo_get_id_url(photo, caption, tags)
    upload_video_get_id_url(video, caption, tags)
    
    list_posts_tags()
    find_id_get_tags(id)
    id_add_tags(id, tags)
    id_del_tags(id, tags)


#### tumblr-cli-uploadr

The main CLI client. To get usage help just run without any parameters:

    $ ./tumblr-cli-uploadr.py

    = tubmlr - command line uploader = (c) 2019 by Robert = version 2020.08.04 =
    
    usage: tumblr-cli-uploadr.py action file "caption" "tag1,tag2"
    
    action  ... photo, video, delete, find-tag, find-id
    file    ... media file to upload
    caption ... markdown formatted text for caption
    tags    ... comma separated values for tags
    
    for configurable options check config file: tumblr-cli-uploadr.json
    
    example:
    tumblr-cli-uploadr.py find-id id              ... find post id and print full json
    tumblr-cli-uploadr.py find-tag tag            ... find the last 20 post(s) tagged with tag tag and print only post id(s)
    tumblr-cli-uploadr.py list-tag id             ... list all tags for post id
    tumblr-cli-uploadr.py list-tag all            ... list all tags for all (the last 20) posts (all = * = -)
    tumblr-cli-uploadr.py list-posts              ... list all (the last 20) posts (print only post id(s))
    tumblr-cli-uploadr.py delete-id id            ... delete post id
    tumblr-cli-uploadr.py delete-id all           ... delete all (the last 20) posts (all = * = -)
    tumblr-cli-uploadr.py delete-tagged tag       ... delete all (the last 20) post tagged with tag tag
    tumblr-cli-uploadr.py add-tag tag1,tag2 id    ... add tag1 and tag2 to post id
    tumblr-cli-uploadr.py del-tag tag1,tag2 id    ... delete tag1 and tag2 from post id
    tumblr-cli-uploadr.py photo file caption tags ... uploads photo file with caption and tags and print post id and url
    tumblr-cli-uploadr.py video file caption tags ... uploads video file with caption and tags and print post id and url


#### tumblr-cli-uploadr.json

Config file in JSON format. Only the example is provided with .example suffix. 

You have to rename the sample to tumblr-cli-uploadr.json and edit all tokens: 

        <your-consumer-key>
        <your-consumer-secret>
        <your-oauth-token>
        <your-oauth-token-secret>
        <your-blog-name>
        
See [tumblr on GitHub](https://github.com/tumblr/pytumblr) for more details.

Other keys in options section should be self-explanatory.
