# TwitFix

very basic flask server that fixes twitter embeds in discord by using youtube-dl to grab the direct link to the MP4 file and embeds the link to it in a custom page



This does work! but I'm new to flask, so it can probably be improved a great deal.



## How to use (discord side)

just put the url to the server, then /twitfix/, and directly after, the full URL to the tweet you want to embed



## How to run (server side)

this is in a virtual environment, so first you should enter the virtual environment using `source env/bin/activate` and then you can start the server with `python3 twitfix.py`


By default I have the port set to 80, just cause that's what was convenient for me, but it can easily be changed, either using an environment variable, or changing the bottom line of the script itself



this script uses the youtube-dl python module, along with flask



This project is licensed under th **Do What The Fuck You Want Public License**

