# TwitFix

very basic flask server that fixes twitter embeds in discord by using youtube-dl to grab the direct link to the MP4 file and embeds the link to it in a custom page

This does work! but I'm new to flask, so it can probably be improved a great deal.

## How to use (discord side)

just put the url to the server,and directly after, the full URL to the tweet you want to embed

## How to run (server side)

this script uses the youtube-dl python module, along with flask, so install those with pip (you can use `pip install -r requirements.txt`) and start the server with `python twitfix.py` ( will need sudo if you leave it at port 80 )

By default I have the port set to 80, just cause that's what was convenient for me, but it can easily be changed, either using an environment variable, or changing the bottom line of the script itself

This project is licensed under th **Do What The Fuck You Want Public License**

