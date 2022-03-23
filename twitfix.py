from flask import Flask, render_template, request, redirect, Response, send_from_directory, send_file, make_response
from flask_cors import CORS
import youtube_dl
import textwrap
import twitter
import json
import re
import os
import urllib.parse
import urllib.request
from datetime import date

from config import load_configuration
from link_cache import initialize_link_cache
from stats_module import initialize_stats
from storage_module import initialize_storage

app = Flask(__name__)
CORS(app)

pathregex = re.compile("\\w{1,15}\\/(status|statuses)\\/\\d{2,20}")
generate_embed_user_agents = [
    "facebookexternalhit/1.1", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0", 
    "facebookexternalhit/1.1", 
    "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0", 
    "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", 
    "TelegramBot (like TwitterBot)", 
    "Mozilla/5.0 (compatible; January/1.0; +https://gitlab.insrt.uk/revolt/january)", 
    "test"]

# Read config from config.json. If it does not exist, create new.
config = load_configuration()

# If method is set to API or Hybrid, attempt to auth with the Twitter API
if config['config']['method'] in ('api', 'hybrid'):
    auth = twitter.oauth.OAuth(config['api']['access_token'], config['api']['access_secret'], config['api']['api_key'], config['api']['api_secret'])
    twitter_api = twitter.Twitter(auth=auth)

link_cache_system = config['config']['link_cache']
storage_module_type = config['config']['storage_module']
STAT_MODULE = initialize_stats(link_cache_system, config)
LINK_CACHE = initialize_link_cache(link_cache_system, config)
STORAGE_MODULE = initialize_storage(storage_module_type, config)

@app.route('/bidoof/')
def bidoof():
    return redirect("https://cdn.discordapp.com/attachments/291764448757284885/937343686927319111/IMG_20211226_202956_163.webp", 301)

@app.route('/stats/')
def statsPage():
    today = str(date.today())
    stats = STAT_MODULE.get_stats(today)
    return render_template('stats.html', embeds=stats['embeds'], downloadss=stats['downloads'], api=stats['api'], linksCached=stats['linksCached'], date=today)

@app.route('/latest/')
def latest():
    return render_template('latest.html')

@app.route('/copy.svg') # Return a SVG needed for Latest
def icon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'copy.svg',mimetype='image/svg+xml') 

@app.route('/font.ttf') # Return a font needed for Latest
def font():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'NotoColorEmoji.ttf',mimetype='application/octet-stream') 

@app.route('/top/') # Try to return the most hit video
def top():
    try:
        [vnf]   = LINK_CACHE.get_links_from_cache('hits', 1, 0)
    except ValueError:
        print(" ➤ [ ✔ ] Top video page loaded: None yet...")
        return make_response('', 204)
    desc    = re.sub(r' http.*t\.co\S+', '', vnf['description'])
    urlUser = urllib.parse.quote(vnf['uploader'])
    urlDesc = urllib.parse.quote(desc)
    urlLink = urllib.parse.quote(vnf['url'])
    print(" ➤ [ ✔ ] Top video page loaded: " + vnf['tweet'] )
    return render_template('inline.html', page="Top", vidlink=vnf['url'], vidurl=vnf['url'], desc=desc, pic=vnf['thumbnail'], user=vnf['uploader'], video_link=vnf['url'], color=config['config']['color'], appname=config['config']['appname'], repo=config['config']['repo'], url=config['config']['url'], urlDesc=urlDesc, urlUser=urlUser, urlLink=urlLink, tweet=vnf['tweet'])

@app.route('/api/latest/')  # Return some raw VNF data sorted by top tweets
def apiLatest():
    tweets   = request.args.get("tweets", default=10, type=int)
    page     = request.args.get("page", default=0, type=int)

    if tweets > 15:
        tweets = 1

    vnf      = LINK_CACHE.get_links_from_cache('_id', tweets, tweets*page)

    print(" ➤ [ ✔ ] Latest video API called")
    STAT_MODULE.add_to_stat('api')
    return Response(response=json.dumps(vnf, default=str), status=200, mimetype="application/json")

@app.route('/api/top/') # Return some raw VNF data sorted by top tweets
def apiTop():
    tweets   = request.args.get("tweets", default=10, type=int)
    page     = request.args.get("page", default=0, type=int)

    if tweets > 15:
        tweets = 1

    vnf      = LINK_CACHE.get_links_from_cache('hits', tweets, tweets*page)

    print(" ➤ [ ✔ ] Top video API called")
    STAT_MODULE.add_to_stat('api')
    return Response(response=json.dumps(vnf, default=str), status=200, mimetype="application/json")

@app.route('/api/stats/') # Return a json of a usage stats for a given date (defaults to today)
def apiStats():
    try:
        STAT_MODULE.add_to_stat('api')
        today = str(date.today())
        desiredDate = request.args.get("date", default=today, type=str)
        stat = STAT_MODULE.get_stats(desiredDate)
        print (" ➤ [ ✔ ] Stats API called")
        return Response(response=json.dumps(stat, default=str), status=200, mimetype="application/json")
    except:
        print (" ➤ [ ✔ ] Stats API failed")

@app.route('/') # If the useragent is discord, return the embed, if not, redirect to configured repo directly
def default():
    user_agent = request.headers.get('user-agent')
    if user_agent in generate_embed_user_agents:
        return message("TwitFix is an attempt to fix twitter video embeds in discord! created by Robin Universe :)\n\n💖\n\nClick me to be redirected to the repo!")
    else:
        return redirect(config['config']['repo'], 301)

@app.route('/oembed.json') #oEmbed endpoint
def oembedend():
    desc  = request.args.get("desc", None)
    user  = request.args.get("user", None)
    link  = request.args.get("link", None)
    ttype = request.args.get("ttype", None)
    return  oEmbedGen(desc, user, link, ttype)

@app.route('/<path:sub_path>') # Default endpoint used by everything
def twitfix(sub_path):
    user_agent = request.headers.get('user-agent')
    match = pathregex.search(sub_path)
    print(request.url)

    if request.url.startswith("https://d.fx"): # Matches d.fx? Try to give the user a direct link
        if user_agent in generate_embed_user_agents:
            print( " ➤ [ D ] d.fx link shown to discord user-agent!")
            if request.url.endswith(".mp4") and "?" not in request.url:
                return dl(sub_path)
            else:
                return message("To use a direct MP4 link in discord, remove anything past '?' and put '.mp4' at the end")
        else:
            print(" ➤ [ R ] Redirect to MP4 using d.fxtwitter.com")
            return dir(sub_path)

    elif request.url.endswith(".mp4") or request.url.endswith("%2Emp4"):
        twitter_url = "https://twitter.com/" + sub_path
        
        if "?" not in request.url:
            clean = twitter_url[:-4]
        else:
            clean = twitter_url

        return dl(clean)

    elif request.url.endswith("/1") or request.url.endswith("/2") or request.url.endswith("/3") or request.url.endswith("/4") or request.url.endswith("%2F1") or request.url.endswith("%2F2") or request.url.endswith("%2F3") or request.url.endswith("%2F4"):
        twitter_url = "https://twitter.com/" + sub_path
        
        if "?" not in request.url:
            clean = twitter_url[:-2]
        else:
            clean = twitter_url

        image = ( int(request.url[-1]) - 1 )
        return embed_video(clean, image)

    if match is not None:
        twitter_url = sub_path

        if match.start() == 0:
            twitter_url = "https://twitter.com/" + sub_path

        if user_agent in generate_embed_user_agents:
            res = embed_video(twitter_url)
            return res

        else:
            print(" ➤ [ R ] Redirect to " + twitter_url)
            return redirect(twitter_url, 301)
    else:
        return message("This doesn't appear to be a twitter URL")

@app.route('/other/<path:sub_path>') # Show all info that Youtube-DL can get about a video as a json
def other(sub_path):
    otherurl = request.url.split("/other/", 1)[1].replace(":/","://")
    print(" ➤ [ OTHER ]  Other URL embed attempted: " + otherurl)
    res = embed_video(otherurl)
    return res

@app.route('/info/<path:sub_path>') # Show all info that Youtube-DL can get about a video as a json
def info(sub_path):
    infourl = request.url.split("/info/", 1)[1].replace(":/","://")
    print(" ➤ [ INFO ] Info data requested: " + infourl)
    with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        result = ydl.extract_info(infourl, download=False)

    return result

@app.route('/dl/<path:sub_path>') # Download the tweets video, and rehost it
def dl(sub_path):
    print(' ➤ [[ !!! TRYING TO DOWNLOAD FILE !!! ]] Downloading file from ' + sub_path)
    url   = sub_path
    match = pathregex.search(url)
    if match is not None:
        twitter_url = url
        if match.start() == 0:
            twitter_url = "https://twitter.com/" + url
    
    mp4link  = direct_video_link(twitter_url)

    cache_hit, stored_identifier = STORAGE_MODULE.store_media(mp4link)
    if not cache_hit:
        STAT_MODULE.add_to_stat('downloads')
    response = STORAGE_MODULE.retrieve_media(stored_identifier)

    if response is None:
        return make_response('', 404)
    if response['output'] == "url":
        return redirect(response['url'])
    if response['output'] == "file":
        r = send_file(response['content'])
        r.headers.update({
            "max-age": 3600,
            "Content-Type": "video/mp4",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })
        return r
    return make_response('', 404)

@app.route('/dir/<path:sub_path>') # Try to return a direct link to the MP4 on twitters servers
def dir(sub_path):
    user_agent = request.headers.get('user-agent')
    url   = sub_path
    match = pathregex.search(url)
    if match is not None:
        twitter_url = url

        if match.start() == 0:
            twitter_url = "https://twitter.com/" + url

        if user_agent in generate_embed_user_agents:
            res = embed_video(twitter_url)
            return res

        else:
            print(" ➤ [ R ] Redirect to direct MP4 URL")
            return direct_video(twitter_url)
    else:
        return redirect(url, 301)

@app.route('/favicon.ico') # This shit don't work
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

def add_link_to_cache(video_link, vnf):
    res = LINK_CACHE.add_link_to_cache(video_link, vnf)
    if res:
        STAT_MODULE.add_to_stat('linksCached')
    return res

def get_link_from_cache(video_link):
    res = LINK_CACHE.get_link_from_cache(video_link)
    if res:
        STAT_MODULE.add_to_stat('embeds')
    return res

def direct_video(video_link): # Just get a redirect to a MP4 link from any tweet link
    cached_vnf = get_link_from_cache(video_link)
    if cached_vnf is None:
        try:
            vnf = link_to_vnf(video_link)
            add_link_to_cache(video_link, vnf)
            return redirect(vnf['url'], 301)
            print(" ➤ [ D ] Redirecting to direct URL: " + vnf['url'])
        except Exception as e:
            print(e)
            return message("Failed to scan your link!")
    else:
        return redirect(cached_vnf['url'], 301)
        print(" ➤ [ D ] Redirecting to direct URL: " + vnf['url'])

def direct_video_link(video_link): # Just get a redirect to a MP4 link from any tweet link
    cached_vnf = get_link_from_cache(video_link)
    if cached_vnf is None:
        try:
            vnf = link_to_vnf(video_link)
            add_link_to_cache(video_link, vnf)
            return vnf['url']
            print(" ➤ [ D ] Redirecting to direct URL: " + vnf['url'])
        except Exception as e:
            print(e)
            return message("Failed to scan your link!")
    else:
        return cached_vnf['url']
        print(" ➤ [ D ] Redirecting to direct URL: " + vnf['url'])

def embed_video(video_link, image=0): # Return Embed from any tweet link
    cached_vnf = get_link_from_cache(video_link)

    if cached_vnf is None:
        try:
            vnf = link_to_vnf(video_link)
            add_link_to_cache(video_link, vnf)
            return embed(video_link, vnf, image)

        except Exception as e:
            print(e)
            return message("Failed to scan your link!")
    else:
        return embed(video_link, cached_vnf, image)

def tweetInfo(url, tweet="", desc="", thumb="", uploader="", screen_name="", pfp="", tweetType="", images="", hits=0, likes=0, rts=0, time="", qrt={}): # Return a dict of video info with default values
    vnf = {
        "tweet"         : tweet,
        "url"           : url,
        "description"   : desc,
        "thumbnail"     : thumb,
        "uploader"      : uploader,
        "screen_name"   : screen_name,
        "pfp"           : pfp,
        "type"          : tweetType,
        "images"        : images,
        "hits"          : hits,
        "likes"         : likes,
        "rts"           : rts,
        "time"          : time,
        "qrt"           : qrt
    }
    return vnf

def link_to_vnf_from_api(video_link):
    print(" ➤ [ + ] Attempting to download tweet info from Twitter API")
    twid = int(re.sub(r'\?.*$','',video_link.rsplit("/", 1)[-1])) # gets the tweet ID as a int from the passed url
    tweet = twitter_api.statuses.show(_id=twid, tweet_mode="extended")
    #print(tweet)
    print(" ➤ [ + ] Tweet Type: " + tweetType(tweet))
    # Check to see if tweet has a video, if not, make the url passed to the VNF the first t.co link in the tweet
    if tweetType(tweet) == "Video":
        if tweet['extended_entities']['media'][0]['video_info']['variants'][-1]['content_type'] == "video/mp4":
            url   = tweet['extended_entities']['media'][0]['video_info']['variants'][-1]['url']
            thumb = tweet['extended_entities']['media'][0]['media_url']
        else:
            url   = tweet['extended_entities']['media'][0]['video_info']['variants'][-2]['url']
            thumb = tweet['extended_entities']['media'][0]['media_url']
    elif tweetType(tweet) == "Text":
        url   = ""
        thumb = ""
    else:
        imgs = ["","","",""]
        i = 0
        for media in tweet['extended_entities']['media']:
            imgs[i] = media['media_url_https']
            i = i + 1

        #print(imgs)

        url   = ""
        images= imgs
        thumb = tweet['extended_entities']['media'][0]['media_url_https']

    qrt = {}

    if 'quoted_status' in tweet:
        qrt['desc']       = tweet['quoted_status']['full_text']
        qrt['handle']     = tweet['quoted_status']['user']['name']
        qrt['screenname'] = tweet['quoted_status']['user']['screen_name']

    text = tweet['full_text']

    vnf = tweetInfo(url, video_link, text, thumb, tweet['user']['name'], tweet['user']['screen_name'], tweet['user']['profile_image_url'], tweetType(tweet), likes=tweet['favorite_count'], rts=tweet['retweet_count'], time=tweet['created_at'], qrt=qrt, images=imgs)
    return vnf

def link_to_vnf_from_youtubedl(video_link):
    print(" ➤ [ X ] Attempting to download tweet info via YoutubeDL: " + video_link)
    with youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'}) as ydl:
        result = ydl.extract_info(video_link, download=False)
        vnf    = tweetInfo(result['url'], video_link, result['description'].rsplit(' ',1)[0], result['thumbnail'], result['uploader'])
        return vnf

def link_to_vnf(video_link): # Return a VideoInfo object or die trying
    if config['config']['method'] == 'hybrid':
        try:
            return link_to_vnf_from_api(video_link)
        except Exception as e:
            print(" ➤ [ !!! ] API Failed")
            print(e)
            return link_to_vnf_from_youtubedl(video_link)
    elif config['config']['method'] == 'api':
        try:
            return link_to_vnf_from_api(video_link)
        except Exception as e:
            print(" ➤ [ X ] API Failed")
            print(e)
            return None
    elif config['config']['method'] == 'youtube-dl':
        try:
            return link_to_vnf_from_youtubedl(video_link)
        except Exception as e:
            print(" ➤ [ X ] Youtube-DL Failed")
            print(e)
            return None
    else:
        print("Please set the method key in your config file to 'api' 'youtube-dl' or 'hybrid'")
        return None

def message(text):
    return render_template(
        'default.html', 
        message = text, 
        color   = config['config']['color'], 
        appname = config['config']['appname'], 
        repo    = config['config']['repo'], 
        url     = config['config']['url'] )

def embed(video_link, vnf, image):
    print(" ➤ [ E ] Embedding " + vnf['type'] + ": " + vnf['url'])
    
    desc    = re.sub(r' http.*t\.co\S+', '', vnf['description'])
    urlUser = urllib.parse.quote(vnf['uploader'])
    urlDesc = urllib.parse.quote(desc)
    urlLink = urllib.parse.quote(video_link)
    likeDisplay = ("\n─────────────\n ♥ [" + str(vnf['likes']) + "] ⤴ [" + str(vnf['rts']) + "]\n─────────────")
    
    try:
        if vnf['type'] == "Video":
            desc = desc
        elif vnf['qrt'] == {}: # Check if this is a QRT and modify the description
            desc = (desc + likeDisplay)
        else:
            qrtDisplay = ("\n─────────────\n ➤ QRT of " + vnf['qrt']['handle'] + " (@" + vnf['qrt']['screenname'] + "):\n─────────────\n'" + vnf['qrt']['desc'] + "'")
            desc = (desc + qrtDisplay +  likeDisplay)
    except:
        vnf['likes'] = 0; vnf['rts'] = 0; vnf['time'] = 0
        print(' ➤ [ X ] Failed QRT check - old VNF object')
        
    if vnf['type'] == "Text": # Change the template based on tweet type
        template = 'text.html'
    if vnf['type'] == "Image":
        image = vnf['images'][image]
        template = 'image.html'
    if vnf['type'] == "Video":
        urlDesc = urllib.parse.quote(textwrap.shorten(desc, width=220, placeholder="..."))
        template = 'video.html'
    if vnf['type'] == "":
        urlDesc  = urllib.parse.quote(textwrap.shorten(desc, width=220, placeholder="..."))
        template = 'video.html'

    return render_template(
        template, 
        likes      = vnf['likes'], 
        rts        = vnf['rts'], 
        time       = vnf['time'], 
        screenName = vnf['screen_name'], 
        vidlink    = vnf['url'], 
        pfp        = vnf['pfp'],  
        vidurl     = vnf['url'], 
        desc       = desc,
        pic        = image,
        user       = vnf['uploader'], 
        video_link = video_link, 
        color      = config['config']['color'], 
        appname    = config['config']['appname'], 
        repo       = config['config']['repo'], 
        url        = config['config']['url'], 
        urlDesc    = urlDesc, 
        urlUser    = urlUser, 
        urlLink    = urlLink )

def tweetType(tweet): # Are we dealing with a Video, Image, or Text tweet?
    if 'extended_entities' in tweet:
        if 'video_info' in tweet['extended_entities']['media'][0]:
            out = "Video"
        else:
            out = "Image"
    else:
        out = "Text"

    return out


def oEmbedGen(description, user, video_link, ttype):
    out = {
            "type"          : ttype,
            "version"       : "1.0",
            "provider_name" : config['config']['appname'],
            "provider_url"  : config['config']['repo'],
            "title"         : description,
            "author_name"   : user,
            "author_url"    : video_link
            }

    return out

if __name__ == "__main__":
    app.config['SERVER_NAME']='localhost:80'
    app.run(host='0.0.0.0')
