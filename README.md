# IQDB Image Search Bot

Telegram bot that searches images via iqdb.org service with fallback
to general-purpose reverse image searching services like google or tineye.

Instance: [@iqdbsearchbot](tg://resolve?domain=iqdbsearchbot)

## Features:

* Handles image hyperlinks
* You can send multiple images at once (telegram album)
* Best match information by IQDB
* Fallback to google, yandex, sausenao, ascii2d and tineye
* Relatively high performance (uses mtproto api instead of bot api)
* Low-latency without any webhooks (same reason)

## Local installation 

```bash
git clone https://git.paulll.cc/paulll/iqdb-search-bot && cd iqdb-search-bot
python3 -m pip install -r requirements.txt
```

You may also need [seaweeedfs](https://github.com/seaweedfs/seaweedfs) instance or anything that can share files over http.
Configure it in `src/img_handler.py`: `def upload(file_path)` should make file `file_path` publically available over http, and return its URL. That's optional and impacts only fallback search.

Meanwhile, you have to get an API token from [@botfather](tg://resolve?domain=botfather) and an api id/hash pair from [my.telegram.org](https://my.telegram.org).
Specify them in `src/secrets.py`. To start your bot, run:

```bash
python3 app.py
```

## Kubernetes deployment

Via [werf](https://github.com/werf/werf). Run something like `werf converge --dev --repo=your-private-registry/repo` after configuring secrets. 

