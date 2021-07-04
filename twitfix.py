from flask import Flask, render_template
import youtube_dl
import json
import re

ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
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

        if twitter_url in link_cache:
            print("Link located in cache")
            return render_template('index.html', vidurl=link_cache[twitter_url]['url'], tweet=link_cache[twitter_url]['description'], pic=link_cache[twitter_url]['thumbnail'], user=link_cache[twitter_url]['uploader'], tweeturl=twitter_url)
        else:
            with ydl:
                try:
                    print("Link not in cache, downloading and adding details to cache file")
                    result = ydl.extract_info(twitter_url, download=False)
                    
                    link_cache[twitter_url] = {
                        "url"           :result['url'],
                        "description"   :result['description'],
                        "thumbnail"     :result['thumbnail'],
                        "uploader"      :result['uploader']
                    }

                    with open("links.json", "w") as outfile: 
                        json.dump(link_cache, outfile, indent=4, sort_keys=True)

                except Exception: # Just to keep from 500s that are messy
                    print(Exception)
                    return "Bad twitter link, try again"

            return render_template('index.html', vidurl=result['url'], tweet=result['description'], pic=result['thumbnail'], user=result['uploader'], tweeturl=twitter_url)
    else:
        print("Link invalid")
        return "Please use a twitter link"

@app.route('/info/<path:subpath>')
def info(subpath):
    with ydl:
        result = ydl.extract_info(subpath, download=False)

    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
