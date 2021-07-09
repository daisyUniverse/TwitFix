from flask import Flask, render_template, request
import pymongo
import youtube_dl
import json
import re

app = Flask(__name__)
pathregex = re.compile("\\w{1,15}\\/status\\/\\d{19}")

link_cache_system = "json" # Select your prefered link cache system, "db" for mongoDB or "json" for locally writing a json file ( not great if using multiple workers )

if link_cache_system == "json":
    link_cache = {}
    f = open('links.json',)
    link_cache = json.load(f)
    f.close()
elif link_cache_system == "db":
    client = pymongo.MongoClient("PUT YOUR MONGODB URL HERE")
    db = client.TwitFix

@app.route('/')
def default():
    return render_template('default.html', message="TwitFix is an attempt to fix twitter video embeds in discord! created by Robin Universe :) 💖 ")

@app.route('/oembed.json')
def oembedend():
    desc = request.args.get("desc", None)
    user = request.args.get("user", None)
    link = request.args.get("link", None)
    return oEmbedGen(desc,user,link)

@app.route('/<path:subpath>')
def twitfix(subpath):

    match = pathregex.search(subpath)
    if match is not None:
        twitter_url = subpath

        if match.start() == 0:
            twitter_url = "https://twitter.com/" + subpath

        res = embedVideo(twitter_url)
        return res
    else:
        return render_template('default.html', message="This doesn't seem to be a twitter link, try /other/ to see if other kinds of video link works? (experimental)")

@app.route('/other/<path:subpath>') # Show all info that Youtube-DL can get about a video as a json
def other(subpath):
    res = embedVideo(subpath)
    return res

@app.route('/info/<path:subpath>') # Show all info that Youtube-DL can get about a video as a json
def info(subpath):
    with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        result = ydl.extract_info(subpath, download=False)

    return result

def embedVideo(vidlink): # Return a render template from a video url
    if link_cache_system == "db":
        collection = db.linkCache
        dbresult = collection.find_one({'tweet': vidlink})
        if dbresult != None:
            print("Link located in DB cache")
            return render_template('index.html', vidurl=dbresult['url'], desc=dbresult['description'], pic=dbresult['thumbnail'], user=dbresult['uploader'], vidlink=vidlink)
        else:
            with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
                try:
                    print("Link not in json cache, downloading and adding details to cache file")
                    result = ydl.extract_info(vidlink, download=False)
                    vnf = vidInfo(result['url'], vidlink, result['description'], result['thumbnail'], result['uploader'])

                    try:
                        out = db.linkCache.insert_one(vnf)
                        print("Link added to DB cache")
                    except Exception:
                        print("Failed to add link to DB cache")
                    
                    return render_template('index.html', vidurl=vnf['url'], desc=vnf['description'], pic=vnf['thumbnail'], user=vnf['uploader'], vidlink=vidlink)

                except Exception:
                    print("Failed to download link")
                    return render_template('default.html', message="Failed to scan your link!")
    
    elif link_cache_system == "json":
        if vidlink in link_cache:
            print("Link located in json cache")
            return render_template('index.html', vidurl=link_cache[vidlink]['url'], desc=link_cache[vidlink]['description'], pic=link_cache[vidlink]['thumbnail'], user=link_cache[vidlink]['uploader'], vidlink=vidlink)
        else:
            with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
                try:
                    print("Link not in json cache, downloading and adding details to cache file")
                    result = ydl.extract_info(vidlink, download=False)
                    vnf = vidInfo(result['url'], vidlink, result['description'], result['thumbnail'], result['uploader'])
                    link_cache[vidlink] = vnf

                    with open("links.json", "w") as outfile: 
                        json.dump(link_cache, outfile, indent=4, sort_keys=True)

                except Exception: # Just to keep from 500s that are messy
                    print("Failed to download link")
                    return render_template('default.html', message="Failed to scan your link!")

            return render_template('index.html', vidurl=vnf['url'], desc=vnf['description'], pic=vnf['thumbnail'], user=vnf['uploader'], vidlink=vidlink)
    else:
        try:
            with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
                result = ydl.extract_info(subpath, download=False)
                vnf = vidInfo(result['url'], vidlink, result['description'], result['thumbnail'], result['uploader'])
                return render_template('index.html', vidurl=vnf['url'], desc=vnf['description'], pic=vnf['thumbnail'], user=vnf['uploader'], vidlink=vidlink)
        except Exception:
            print("Failed to download link")
            return render_template('default.html', message="Failed to scan your link!")


def vidInfo(url, tweet="", desc="", thumb="", uploader=""): # Return a dict of video info with default values
    vnf = {
        "tweet"         :tweet,
        "url"           :url,
        "description"   :desc,
        "thumbnail"     :thumb,
        "uploader"      :uploader
    }
    return vnf

def oEmbedGen(description, user, vidlink):
    out = {
            "type":"video",
            "version":"1.0",
            "provider_name":"TwitFix",
            "provider_url":"https://github.com/robinuniverse/twitfix",
            "title":description,
            "author_name":user,
            "author_url":vidlink
            }

    return out

if __name__ == "__main__":
    app.run(host='0.0.0.0')
