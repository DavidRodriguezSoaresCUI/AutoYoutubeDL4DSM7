# [AutoYoutubeDL4DSM7](https://gitlab.com/DRSCUI/autoyoutubedl4dsm7)

Do you want to add to your Synology NAS the ability to make backups of Youtube playlists and channels, keep them up to date and all this in a per-user basis ? This may be for you.

Features :
 - Compatible with __public__ and __unlisted__ Youtube playlists (not _private_).
 - Compatible with __age-restricted__ Youtube videos (as long as you have proven Google/Youtube your age) (TODO:check).
 - Set-and-forget install; edit behavior whenever
 - Flexible download location and per-user playlist/channel backup file
 - Faster playlist lookup: diverse tricks to speedup scan for new content (yt-dlp is not optimized for frequent scanning)

## Notations

Please take note of the notations used in this file :
 - `AYDL` : Shorthand for AutoYoutubeDL
 - `<PYTHON>` : Has to be replaced with `python` on windows or `python3` on linux, or the full path to the python interpreter on your system.
 - `<AYDL_SCRIPT_PATH>` : Has to be replaced with `AutoYoutubeDL.py` when launching AYDL from the its location directory, `path/to/AYDL/AutoYoutubeDL.py` otherwise.

## Requirements


You need `Python 3.6` or later installed on your machine and callable from the terminal. [Link to python.org/downloads](https://www.python.org/downloads/)

For required packages see section `Installing dependencies`

>Earlier versions of `Python 3` may work but are unsupported.


## Installing dependencies <a name="#Installing-dependencies"></a>


Simply run (as with privileges if needed) on a terminal :

`<PYTHON> -m pip install --upgrade -r requirements.txt`

This will install or upgrade required packages using `Python`'s integrated package manager `pip`


# Usage


## Using AutoYoutubeDL to keep an up-to-date backup of an evolving playlist

TODO

# Q&A

## How to change video naming format or quality ?

TODO

## How to download __age-restricted__ content

TODO: update following doc

Follow these steps and AYDL should be able to use your own age verification token from your cookies to download __age-restricted__ content. Skip to step 3 if you are already age-verified :

 1. Log in to Youtube, then try to watch any age-restricted video.
 
 2. You should be asked to prove you're an adult. Follow given steps and complete your age verification.
  > There may be a verification delay. Wait until you can actually see __age-restricted__ content before going to step 3.

 3. Follow [this tutorial on how to extract your Youtube cookies](https://brian.carnell.com/articles/2021/downloading-age-restricted-videos-with-youtube-dl/) for later use with AYDL. You should have obtained a file named `youtube.com_cookies.txt`.
  > This tutorial is specific to desktop chrome-based browsers. If you use a mobile browser, a browser not based on chrome or a browser that doesn't allow you to download extensions, you may need to find another way to extract your Youtube cookies or try with a recommended browser.

 4. Place the cookie file `youtube.com_cookies.txt` in the same directory as `AutoYoutubeDL.py`.

