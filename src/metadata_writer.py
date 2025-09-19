from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import APIC

def save_metadata(filepath, new_tags, cover_image_data=None):
    """
    Salva os novos metadados e a capa do álbum em um arquivo de áudio.
    """
    try:
        if filepath.lower().endswith('.mp3'):
            audio = EasyID3(filepath)
            for key, value in new_tags.items():
                audio[key] = value
            audio.save()

            if cover_image_data:
                audio = EasyID3(filepath)
                audio.tags.add(
                    APIC(
                        encoding=3,  # 3 is for utf-8
                        mime='image/jpeg',  # or image/png
                        type=3,  # 3 is for the cover image
                        desc='Cover',
                        data=cover_image_data
                    )
                )
                audio.save()

        elif filepath.lower().endswith('.flac'):
            audio = FLAC(filepath)
            for key, value in new_tags.items():
                audio[key] = value
            
            if cover_image_data:
                pic = Picture()
                pic.data = cover_image_data
                pic.mime = u"image/jpeg"
                pic.type = 3
                audio.add_picture(pic)
            audio.save()

        elif filepath.lower().endswith('.m4a'):
            audio = MP4(filepath)
            for key, value in new_tags.items():
                audio[key] = value
            
            if cover_image_data:
                audio["covr"] = [MP4Cover(cover_image_data, MP4Cover.FORMAT_JPEG)]
            audio.save()
        
        return True

    except Exception as e:
        return False