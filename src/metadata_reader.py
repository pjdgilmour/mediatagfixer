from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3NoHeaderError

def get_metadata(filepath):
    """
    Lê os metadados de um arquivo de áudio.
    Retorna um dicionário com as tags ou None se o arquivo não for suportado.
    """
    try:
        if filepath.lower().endswith('.mp3'):
            audio = EasyID3(filepath)
        elif filepath.lower().endswith('.flac'):
            audio = FLAC(filepath)
        elif filepath.lower().endswith('.m4a'):
            audio = MP4(filepath)
        else:
            return None
        
        tags = {
            'artist': audio.get('artist', [''])[0],
            'album': audio.get('album', [''])[0],
            'title': audio.get('title', [''])[0],
            'tracknumber': audio.get('tracknumber', [''])[0],
            'date': audio.get('date', [''])[0],
        }
        return tags
    except ID3NoHeaderError:
        return None
    except Exception as e:
        return None