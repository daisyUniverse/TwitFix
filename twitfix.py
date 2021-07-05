from flask import Flask, render_template
import youtube_dl
import json
import re

app = Flask(__name__)
pathregex = re.compile("\\w{1,15}\\/status\\/\\d{19}")

link_cache = {}
f = open('links.json',)
link_cache = json.load(f)
f.close()

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
    if vidlink in link_cache:
        print("Link located in cache")
        return render_template('index.html', vidurl=link_cache[vidlink]['url'], desc=link_cache[vidlink]['description'], pic=link_cache[vidlink]['thumbnail'], user=link_cache[vidlink]['uploader'], vidlink=vidlink)
    else:
        with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
            try:
                print("Link not in cache, downloading and adding details to cache file")
                result = ydl.extract_info(vidlink, download=False)
                vnf = vidInfo(result['url'], result['description'], result['thumbnail'], result['uploader'])
                link_cache[vidlink] = vnf

                with open("links.json", "w") as outfile: 
                    json.dump(link_cache, outfile, indent=4, sort_keys=True)

            except Exception: # Just to keep from 500s that are messy
                print("Failed to download link")
                return render_template('default.html', message="Failed to scan your link!")

        return render_template('index.html', vidurl=vnf['url'], desc=vnf['description'], pic=vnf['thumbnail'], user=vnf['uploader'], vidlink=vidlink)

def vidInfo(url, desc="", thumb="", uploader=""): # Return a dict of video info with default values
    vnf = {
        "url"           :url,
        "description"   :desc,
        "thumbnail"     :thumb,
        "uploader"      :uploader
    }
    return vnf

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
