#!/bin/python3
# -*- coding: utf8 -*-
#!pylint: disable=import-error, no-name-in-module, broad-except, import-outside-toplevel, protected-access, possibly-unused-variable, trailing-whitespace, line-too-long, invalid-name

''' 
AutoYoutubeDL is a utility based on yt-dlp that makes it easy to download
or keep up to date a backup of a playlist.

License: see LICENSE file at the root of this repository.
Author: DavidRodriguezSoaresCUI
'''

from DRSlib.debug import debug_var


YDL_FORMAT = {
    "naming_channel": lambda _info: f"./{_info['channel']}/%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s",
    "naming_channel_audio": lambda _info: f"./Audio/{_info['channel']}/%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s",
    "naming_playlist": lambda _info: f"./{_info['channel'][0].upper()}{_info['channel'][1:]} - {_info['title']}/%(playlist_index)03d - %(title)s.%(ext)s",
    "naming_playlist_audio": lambda _info: f"./Audio/{_info['channel'][0].upper()}{_info['channel'][1:]} - {_info['title']}/%(playlist_index)03d - %(title)s.%(ext)s",
    "format": "bestvideo[ext=mp4][height<=?1080]+bestaudio[ext=m4a]/best",
    "format_audio_only": "bestaudio[ext=m4a]/bestaudio"
}

DEFAULT_PLAYLIST_TEXT = '''# Playlist file
# Fill this file with the URL of Youtube playlists/channels you want to AutoYoutubeDL to download for you !
# Remplissez ce fichier d'adresses URL de playlist/chaîne Youtube et AutoYoutubeDL téléchargera son contenu pour vous !
# Note: One URL per line; anything after a # is ignored (you may use it to write playlist/channel name); AutoYoutubeDL runs every hour so you may need to wait
# Note: Une URL par ligne; tout ce qui est à droite d'un # est ignoré (vous pouvez utiliser ça pour écrire le nom de la chaîne/playlist); AutoYoutubeDL s'exécute toutes les heures donc les changements ne sont pas immédiats
# 
# exemple (playlist):
# https://www.youtube.com/playlist?list=PL_x-m9VghzVdmwfpgIBvd_LgR8Bk9nOLD # playlist musique
# exemple (channel):
# https://www.youtube.com/channel/UCn4kr-F4yM3CfDFuRt0WsyQ # chaîne intéressante
# https://www.youtube.com/user/joueurdugrenier # adresse alternative pour une chaîne
# 
# To keep audio files in a separate folder, add [audio] after the URL. Example:
# Pour conserver les fichiers audio séparément, ajoutez [audio] après l'URL. Exemple:
# https://www.youtube.com/playlist?list=PL_x-m9VghzVdmwfpgIBvd_LgR8Bk9nOLD [audio] # playlist musique
#
# To only download audio, use tag "[audio only]" instead. Example:
# Pour ne télécharger que la version audio, utilisez plutôt "[audio only]". Exemple:
# https://www.youtube.com/playlist?list=PL_x-m9VghzVdmwfpgIBvd_LgR8Bk9nOLD [audio only]
# 
'''

############################## imports section ##############################

if __name__=='__main__':

    import argparse
    import configparser
    import datetime
    # import importlib
    import subprocess
    import json
    import logging
    import re
    import sys
    import urllib.request
    from collections import defaultdict
    from pathlib import Path
    from pprint import pformat
    from typing import NoReturn, Tuple, List, Iterable, Callable, Any
    
    # from pprint import pprint

    try:
        import yt_dlp
        from yt_dlp import YoutubeDL
        from yt_dlp.version import __version__ as YTDLP_VERSION
        from yt_dlp.utils import DateRange
    except ModuleNotFoundError:
        print("Couldn't load yt-dlp: Please run `pip install -r requirements.txt`")
        raise
    try:
        # from DRSlib.execute   import execute
        from DRSlib.banner    import bannerize
        from DRSlib.debug     import call_progress
        from DRSlib.spinner   import MySpinner
        from DRSlib.utils     import LOG_FORMAT
    except ModuleNotFoundError:
        print("Couldn't load libraries from DRSlib: Check https://github.com/DavidRodriguezSoaresCUI/DRSlib for installation instructions or run `pip install -r requirements.txt`.")
        raise

    SCRIPT_DIR = Path( __file__ ).resolve().parent
    LOCK = SCRIPT_DIR / 'AutoYoutubeDL.lock'

    # Logging setup
    LOG_LEVEL = logging.DEBUG
    logging.basicConfig( 
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        filename=(SCRIPT_DIR / 'AutoYoutubeDL.log').as_posix(),
        filemode='w'
    )
    LOG = logging.getLogger( __name__ )

    # Log warning/errors to file
    important_h = logging.FileHandler(
        filename=(SCRIPT_DIR / 'WARNING.log').as_posix(),
        mode='a',
        encoding='utf8'
    )
    important_h.setLevel(logging.WARNING)
    # important_h.setFormatter(logging.Formatter(LOG_FORMAT))
    LOG.addHandler(important_h)

PROGRESS_TO_FILE = False
    

############################## Common functions section ##############################

def parse_args() -> argparse.Namespace:
    ''' Get cli args '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--log_progress', action='store_true', help="Intended for monitoring progress without tty")
    
    return parser.parse_args()


@call_progress( "Checking internet availability" )
def internet_available(host: str = 'http://google.com') -> bool:
    ''' from https://www.codespeedy.com/how-to-check-the-internet-connection-in-python/
    '''
    try:
        urllib.request.urlopen(host)
        return True
    except Exception as e:
        print(e)
        return False


# @call_progress( 'Upgrading and importing python module youtube_dl' )
# def upgrade_youtubedl() -> None:
#     ''' Used to try to import and upgrade the youtube-dl module.
#     '''
#     execute( ['python3', '-m', 'pip', 'install', '--upgrade', 'yt-dlp'], shell=False )
#     # LOG.debug( "Stdout: " + " ".join(stdX['stdout'].splitlines()) )
#     _yt_dlp = importlib.reload(yt_dlp)
#     globals()['yt_dlp']    = _yt_dlp
#     globals()['YoutubeDL'] = _yt_dlp.YoutubeDL
#     globals()['YTDLP_VERSION'] = _yt_dlp.version.__version__


def make_default_config_file( destination_file: Path ) -> NoReturn:
    ''' Writes a default config file at given path '''
    assert not destination_file.exists()
    LOG.info("Writing default config to '%s'", destination_file)
    cfg = configparser.ConfigParser()
    ss = 'Settings'
    cfg.add_section(ss)
    cfg.set( ss, 'surveiled_path_help', "Lists paths to scan for AutoYoutubeDL.ini file." )  
    cfg.set( ss, 'surveiled_path', json.dumps(["/example/path"]) )
    with destination_file.open('w',encoding='utf8') as f:
        cfg.write(f)
    print(f"Please fill configuration file {destination_file} before running AutoYoutubeDL again!")
    end()


def load_config( _dir: Path = SCRIPT_DIR ) -> dict:
    ''' Read AutoYoutubeDL.ini file; Returns config as dictionnary
    '''
    cfg_p = _dir / 'AutoYoutubeDL.ini'
    if not cfg_p.is_file():
        make_default_config_file( cfg_p )
    
    LOG.info("Reading default config from '%s'", cfg_p)
    cfg = configparser.ConfigParser()
    cfg.read(str(cfg_p))
    res = {}
    ss = 'Settings'
    assert cfg.has_section(ss), f"Invalid config file {cfg_p}!"
    res['surveiled_path'] = [
        Path(p_s).resolve()
        for p_s in json.loads(cfg.get(ss,'surveiled_path'))
    ]

    return res


def make_default_playlist_file( file_p: Path ) -> None:
    ''' Writes default playlist file '''
    file_p.write_text(DEFAULT_PLAYLIST_TEXT, encoding='utf8')


def surveiled_playlist_files( cfg: dict ) -> Tuple[Path,Path,Path]:
    ''' Makes sure surveiled directories and files exist, then returns 
    tuple: ( <surveiled_path:Path>, <surveiled_playlist_file:Path>, <surveiled_playlist_db:Path> )
    '''
    for p in cfg['surveiled_path']:
        # Make sure p exists
        if not p.is_dir():
            if p.exists():
                LOG.error("Path '%s' exists but not a directory!", p)
                continue
            LOG.warning("Creating '%s' !", p)
            p.mkdir(parents=True)

        # Makes sure playlist file exists
        playlist_file_p = p / "AutoYoutubeDL.txt"
        if not playlist_file_p.is_file():
            make_default_playlist_file( playlist_file_p )
            continue 

        # Makes sure playlist DB file exists
        playlist_db_p = p / "AutoYoutubeDL.json"
        if not playlist_db_p.is_file():
            playlist_db_p.write_text('{}', encoding='utf8')

        yield p, playlist_file_p, playlist_db_p


def playlists_from_file( playlist_f: Path ) -> Tuple[str,bool]:
    ''' Yields ( <playlist_url:str>, <do_extract_audio:bool> ) from playlist file
    '''
    _pattern = re.compile(r"(http\S+)(\s\[.+\])?")
    for line in playlist_f.read_text().splitlines():
        rpos = line.find('#')
        _line = line[:rpos].strip() if rpos!=-1 else line.strip()
        if len(_line)<10:
            continue

        def simplify_str( s: str ) -> str:
            return ''.join( c for c in s.lower() if 'a' <= c <= 'z' ) if s else None

        # line should match pattern
        res = re.match( _pattern, _line )
        if not res:
            LOG.warning("Line '%s' did not match pattern!", _line)
        yield res.group(1), simplify_str(res.group(2))


def end() -> NoReturn:
    ''' Ends program '''
    # Release Lock
    LOCK.unlink(missing_ok=True)
    print("END OF PROGRAM")
    sys.exit(0)

############################## Playlist downloader section ##############################

class YDLDownloadMonitor:
    ''' Used to monitor downloading progress
    '''

    PART_TYPES = {
        '.mp4' : 'video',
        '.webm': 'video',
        '.m4a' : 'audio',
        'UNKNOWN_TYPE': 'UNKNOWS_STREAM'
    }
    CATEGORY = lambda f_name: YDLDownloadMonitor.PART_TYPES[ 
        next( (
            ext for ext in YDLDownloadMonitor.PART_TYPES if ext in f_name),
            'UNKNOWN_TYPE' # default
        ) ]

    def __init__( self ):
        self.seen = set()
        self.spinner = MySpinner()
        self.curr_category = None
        self.curr_id = None

    def hook( self, d ):
        ''' Will be called on downloading progress '''

        if self.curr_category is None:
            self.curr_category = YDLDownloadMonitor.CATEGORY( d['filename'] )
            self.curr_id = Path(d['info_dict']['_filename']).stem

        self.spinner.animation( 
            text="{} ({}): SPD {} - TOT {} - ETA {} {}".format(
                self.curr_id,
                self.curr_category,
                d.get('_speed_str','?'),
                d.get('_total_bytes_str','?'),
                d.get('_eta_str','?'),
                d.get('_percent_str','?'),
            )
        )

        if d.get('status',None)=='error':
            LOG.warning("Download error on %s", self.curr_id)
        if d.get('status',None)=='finished':
            self.seen.add( self.curr_id )
            self.spinner.animation( text=f"{self.curr_id} ({self.curr_category}): DONE! \n", no_spinner=True )
            self.curr_category, self.curr_id = None, None

class FakeLogger(logging.Logger):
    ''' Interface for ProgressMonitor
    Yes I understand it is mostly redundant
    '''

    def __init__(self) -> None:
        super().__init__('FakeLogger', level=logging.DEBUG)

    def debug( self, *args, **kwargs ) -> None:
        pass

    def warning( self, *args, **kwargs ):
        pass

    def info( self, *args, **kwargs ):
        pass

    def error( self, *args, **kwargs ):
        pass

class ProgressMonitor(FakeLogger):
    ''' Hacky way of monitoring playlist/channel download progress with a Logger '''
    def __init__(self) -> None:
        super().__init__()
        self.pattern = re.compile(r"\[download\] Downloading video ([0-9]+) of ([0-9]+)")

    def debug( self, *args, **kwargs ) -> None:
        msg = args[0]
        res = re.match(self.pattern, msg)
        if res:
            LOG.info("[%s/%s]", res.group(1), res.group(2))

class YDLPostProcessMonitor:
    ''' Used to monitor post-downloading progress '''
    
    def __init__(self):
        self._merged = set()
        self._successful_downloads = set()
        self._audio_only = False

    @property
    def successful_downloads( self ) -> List[int]:
        ''' Converts to list '''
        return list(self._successful_downloads)

    def hook( self, d: dict ):
        ''' Will be called on post-downloading progress '''
        if d['status']=='finished':
            if d['postprocessor']=='MoveFiles' and self._audio_only:
                self._successful_downloads.add( d['info_dict']['playlist_index'] )
            elif d['postprocessor']=='Merger':
                self._merged.add( d['info_dict']['playlist_index'] )
            elif d['postprocessor']=='MoveFiles' and d['info_dict']['playlist_index'] in self._merged:
                self._successful_downloads.add( d['info_dict']['playlist_index'] )


def output_template( playlist: dict, audio: bool = False ) -> str:
    ''' Returns appropriate naming format, applies ``YDL_FORMAT`` formatter.
    '''
    s = 'naming_' + ('channel' if playlist['is_channel'] else 'playlist') + ('_audio' if audio else '')
    formatter = YDL_FORMAT[s]
    return formatter( playlist['infos'] )


def download_playlist( playlist: dict, download_dir: Path ) -> List[int]:
    ''' Downloads playlist, then returns list of successful download indexes '''

    LOG.info("Processing playlist '%s' ..", playlist['title'])

    down_monitor = YDLDownloadMonitor()
    postp_monitor = YDLPostProcessMonitor()
    ydl_opts = { 
        'format'  : YDL_FORMAT['format'],
        'outtmpl' : { 'default': output_template(playlist) },
        'ignoreerrors' : True,
        'progress_hooks': [down_monitor.hook],
        'postprocessor_hooks': [postp_monitor.hook],
        'paths': { 'home': download_dir.as_posix() },
        'simulate': False,
        'logger': ProgressMonitor() if PROGRESS_TO_FILE else None
    } # 'verbose': True, 'logger': LOG, 'quiet': True
    # 'postprocessors': [{
    #         # Embed metadata in video using ffmpeg.
    #         'key': 'FFmpegEmbedSubtitle'
    #     },{
    #         # Embed metadata in video using ffmpeg.
    #         # See yt_dlp.postprocessor.FFmpegMetadataPP for the arguments it accepts
    #         'key': 'FFmpegMetadata',
    #         'add_chapters': True,
    #         'add_metadata': True,
    #     }],
    

    # What items to download: specific or all
    if playlist['items_completed'] and not playlist['is_channel']:
        indexes_to_process = [
            str(x+1)
            for x in range(playlist['len'])
            if x+1 not in playlist['items_completed']
        ]
        if len(indexes_to_process) < 1:
            LOG.info("Nothing to download!")
            return None
        ydl_opts['playlist_items'] = ','.join(indexes_to_process)
    elif playlist['is_channel'] and 'last_scan' in playlist:
        ydl_opts['dateafter'] = DateRange( start=playlist['last_scan'] )
        LOG.debug("Download items on dates: %s", ydl_opts['dateafter'])
    else:
        ydl_opts['playliststart'] = 1

    # Cookies
    # cookies_file_absolute_path = SCRIPT_DIR / "youtube.com_cookies.txt"
    # if cookies_file_absolute_path.is_file():
    #     LOG.debug("Setting cookie file=%s", cookies_file_absolute_path)
    #     ydl_opts['cookiefile'] = str(cookies_file_absolute_path)

    def run_YDL( options: dict, url: str ) -> None:    
        # run YoutubeDL on utl
        try:
            LOG.debug("Running YoutubeDL with parameters: %s", pformat(options))
            with YoutubeDL(options) as ydl:
                ydl.download( [ url ] )
        except Exception as e:
            LOG.error("YoutubeDL failed on '%s'; check error message.\ne=%s", url, e)
            raise

    # normal download
    skip_video_download = playlist['do_extract_audio'] is not None and 'audio' in playlist['do_extract_audio'] and 'only' in playlist['do_extract_audio']
    if not skip_video_download:
        run_YDL( ydl_opts, playlist['url'] )

    # audio-only download
    if playlist['do_extract_audio'] is not None:
        # We need to edit options quite a bit
        for k in ('progress_hooks', 'postprocessor_hooks'):
            if k in ydl_opts:
                del ydl_opts[k]
        if skip_video_download:
            # Progress tracking requires at least a postprocessor hook on audio downloading
            postp_monitor._audio_only = True
            ydl_opts['postprocessor_hooks'] = [postp_monitor.hook]
        ydl_opts['format'] = YDL_FORMAT['format_audio_only']
        ydl_opts['outtmpl'] = { 'default': output_template( playlist, audio=True ) }
        # Run Ydl again
        run_YDL( ydl_opts, playlist['url'] )

    successful_downloads = postp_monitor.successful_downloads
    LOG.info("Downloaded %s videos for '%s' !", len(successful_downloads), playlist['title'])
    return successful_downloads


# Deprecated because reading titles breaks too much and it is good enough to for the
# user to set it up
def get_playlist_infos( url: str = None ) -> tuple:
    ''' Tries to obtain playlist title and size
    Returns: ( <infos:dict>, <title:str>, <size:int>, <is_channel:bool>, <latest_video_id:str> )
    '''
    try:
        LOG.info("Fetching playlist infos for '%s'. This could take a moment ..", url)
        with YoutubeDL( { 'quiet':True,'ignoreerrors':True } ) as ydl:
            # The following alternative is a butchered code rip from `YoutubeDL.py` (faster for simple info)
            for ie_key, ie in ydl._ies.items():
                if not ie.suitable(url):
                    continue
                tmp = ydl.get_info_extractor(ie_key).extract(url)
                if 'title' not in tmp or tmp['title']==tmp['id']:
                    LOG.warning("Could not resolve title; utl=`%s`;data=`%s`", url,tmp)

                # Channel
                if tmp['title']==f"{tmp['channel']} - Videos" or url==tmp['channel_url']:
                    entries = list( tmp['entries'] )
                    return tmp, tmp['channel'], len(entries), True, entries[0]['id']
                # Playlist
                fulltitle = f"{tmp['channel'][0].upper()}{tmp['channel'][1:]} - {tmp['title']}"
                return tmp, fulltitle, sum(1 for _ in tmp['entries']), False, None
    except Exception as e:
        print(f"YoutubeDL failed to obtain the playlist title. Perhaps you mistyped the URL or the playlist is private (in which case a solution would be to make it unlisted or public). error : {e}")
        raise


def log_date() -> None:
    ''' for activity monitoring '''
    with (SCRIPT_DIR / 'AutoYoutubeDL.run.log').open('a') as f:
        f.write(f"{datetime.datetime.now()}\n")


def check_for_unmuxed_videos(root: Path) -> None:
    ''' Unfortunately it happens that some videos don't get muxed,
    leaving corresponding .mp4 and .m4a files instead.
    This attempts to fix it.
    '''
    def group_by(elements: Iterable[Any], criterion: Callable) -> dict:
        res = defaultdict(list)
        for e in elements:
            res[criterion(e)].append(e)
        return res

    def mux_mp4(destination_title: str, mp4_video: Path, m4a_audio: Path) -> None:
        LOG.info("Muxing %s ..", destination_title)
        command = [
            'ffmpeg',
            '-i', mp4_video,
            '-i', m4a_audio,
            '-c', 'copy',
            '-loglevel', 'info',
            (mp4_video.parent / destination_title)
        ]
        output = subprocess.check_output(command, shell=False, universal_newlines=True, stderr=subprocess.STDOUT)
        # On success, last line FFmpeg ouputs contains stats. Here we check for them.
        if 'muxing overhead' not in output:
            raise RuntimeError(f"FFmpeg failed; check output for errors:\n{output}")
        mp4_video.unlink()
        m4a_audio.unlink()

    is_unmuxed_file = lambda file_path_stem: len(file_path_stem)>5 and file_path_stem[-5:-3]=='.f'
    unmuxed_files = list(
        _file
        for _file in root.rglob('*.*')
        if is_unmuxed_file(_file.stem)
    )
    if not unmuxed_files:
        LOG.info("Non unmuxed video found!")

    actual_title = lambda _f: _f.stem if len(_f.stem)<6 else _f.stem[:-5]
    unmuxed_file_couples = group_by(unmuxed_files, actual_title)
    LOG.info("Found %d unmuxed videos!", len(list(unmuxed_file_couples.keys())))

    for title,elements in unmuxed_file_couples.items():
        if len(elements)!=2:
            LOG.warning("%d elements for title='%s', elements=%s", len(elements), title, elements)
            continue

        video_components = group_by(elements, lambda x: x.suffix)
        if not all(k in video_components for k in ('.mp4','.m4a')):
            LOG.warning("video_components=%s", video_components)
            continue

        mux_mp4( 
            destination_title=(title + '.mp4'),
            mp4_video=video_components['.mp4'][0],
            m4a_audio=video_components['.m4a'][0]
        )
        

############################## 'main' section ##############################

@bannerize(style='lean')
def main() -> None:
    ''' Main '''

    # fetch arguments
    cmd_args = parse_args()

    global PROGRESS_TO_FILE
    PROGRESS_TO_FILE = cmd_args.log_progress
    LOG.info("PROGRESS_TO_FILE=%s", PROGRESS_TO_FILE)

    # if not internet_available( host="http://www.youtube.com" ):
    #     print("Couldn't reach Youtube. Please check connection.")
    #     end()

    # upgrade and import youtube_dl
    #upgrade_youtubedl()
    cfg = load_config()
    for surveiled_path_p, surveiled_playlist_p, surveiled_playlist_db in surveiled_playlist_files(cfg):
        LOG.info("Processing playlists in %s ..", surveiled_playlist_p)
        
        # Load DB
        _db = json.loads(surveiled_playlist_db.read_text(), )
        
        # process playlists
        for playlist_url_s, do_extract_audio in playlists_from_file(surveiled_playlist_p):
            try:
                playlist_infos, playlist_title, playlist_len, playlist_is_yt_channel, latest_video_id = get_playlist_infos(playlist_url_s)
            except yt_dlp.utils.ExtractorError:
                LOG.warning("Playlist %s does not exist or is private!", playlist_url_s)
                continue
            
            if playlist_url_s not in _db:
                LOG.info("Added new playlist/channel: %s", playlist_title)
                _db[playlist_url_s] = {
                    'title': playlist_title
                }
            elif _db[playlist_url_s]['title']!=playlist_title:
                LOG.warning("Playlist title mismatch: _db[playlist_url_s]['title']=%s, playlist_title=%s", _db[playlist_url_s]['title'], playlist_title)
            
            # Restriction: scan channels only if a new video was uploaded
            if playlist_is_yt_channel:
                # if _db[playlist_url_s].get('last_scan') == (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d"):
                #     LOG.info("Skipping channel scan: Already scanned today.")
                #     continue
                if _db[playlist_url_s].get('last_video_id') == latest_video_id:
                    LOG.info("Skipping channel scan: No new video detected.")
                    continue
            
            successful_downloads = download_playlist(
                playlist={
                    'url'  : playlist_url_s,
                    'title': _db[playlist_url_s]['title'],
                    'len'  : playlist_len,
                    'is_channel': playlist_is_yt_channel,
                    'items_completed' : _db[playlist_url_s].get('done'),
                    'last_scan' : _db[playlist_url_s].get('last_scan'),
                    'do_extract_audio': do_extract_audio,
                    'infos': playlist_infos
                },
                download_dir=surveiled_path_p
            )
            
            # Save progress
            if playlist_is_yt_channel:
                LOG.debug("Scan done")
                _db[playlist_url_s]['last_scan'] = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y%m%d")
                _db[playlist_url_s]['last_video_id'] = latest_video_id
            elif successful_downloads:
                LOG.debug("Successfully downloaded %s", successful_downloads)
                debug_var(_db[playlist_url_s].get('done',[]))
                _db[playlist_url_s]['done'] = _db[playlist_url_s].get('done',[]) + successful_downloads
                debug_var(_db[playlist_url_s]['done'])
            else:
                LOG.debug("Did nothing")

            # Save DB
            surveiled_playlist_db.write_text(
                json.dumps(_db, indent=2),
                encoding='utf8'
            )

        check_for_unmuxed_videos(surveiled_path_p)


if __name__=='__main__':
    
    if LOCK.is_file():
        # Lock file present => abort
        LOG.warning("Lock file detected: aborting execution")
        sys.exit(0)
    if not any( x in sys.argv for x in ('-h','--help') ):
        # Lock file abscent + not lauching help => create lock
        LOCK.touch()
    try:
        log_date()
        main()
    except Exception:
        pass
    end()
