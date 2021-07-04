from flask import Flask, render_template
import youtube_dl
import re

ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
app = Flask(__name__)
pathregex = re.compile("\\w{1,15}\\/status\\/\\d{19}")

@app.route('/<path:subpath>')
def twitfix(subpath):

    match = pathregex.search(subpath)
    if match is not None:
        twitter_url = subpath

        if match.start() == 0:
            twitter_url = "https://twitter.com/" + subpath

        with ydl:
            try:
                result = ydl.extract_info(twitter_url, download=False)
            except Exception: # Just to keep from 500s that are messy
                return "Bad twitter link, try again"

        return render_template('index.html', vidurl=result['url'], tweet=result['description'], pic=result['thumbnail'], user=result['uploader'], tweeturl=twitter_url)
    else:
        return "Please use a twitter link"

@app.route('/info/<path:subpath>')
def info(subpath):
    with ydl:
        result = ydl.extract_info(subpath, download=False)

    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
