Clone the repo:
```git clone --recursive https://github.com/evansloan082/mumble-youtube-player.git ```

Install requirements:
```pip install -r requirements.txt```

Get Google Service Account Credentials:
https://developers.google.com/identity/protocols/OAuth2ServiceAccount

Replace service_client.json with your own credentials. (Make sure it is still named service_client.json)

Modify config/config.ini as you see fit

Run the bot:
```python main.py```

Python 3.6 required

Having trouble getting this to fetch songs with youtube-dl when using a virtual env on MacOS. Works fine with virtual env on ubuntu, not tested on Windows
