from flask import Flask, render_template, url_for, request, redirect
from datetime import datetime
import youtube_dl
import requests
import psutil
import os

ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
app = Flask(__name__)

@app.route('/twitfix/<path:subpath>')
def twitfix(subpath):
    if subpath.startswith('https://twitter.com'):
        with ydl:
            result = ydl.extract_info(subpath, download=False)

        return render_template('index.html', vidurl=result['url'], tweet=result['description'], pic=result['thumbnail'], user=result['uploader'], tweeturl=subpath)
    else:
        return "Please use a twitter link"

@app.route('/info/<path:subpath>')
def info(subpath):
    with ydl:
        result = ydl.extract_info(subpath, download=False)

    return result

if __name__ == "__main__":
    app.run(debug=False)
    app.run(host='0.0.0.0', port=80)
