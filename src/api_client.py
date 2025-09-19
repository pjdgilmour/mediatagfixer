import acoustid
import musicbrainzngs
import discogs_client

# ATENÇÃO: Substitua 'SUA_CHAVE_DE_API' pela sua chave de cliente do AcoustID.
# Você pode obter uma em https://acoustid.org/
ACOUSTID_API_KEY = 'SUA_CHAVE_DE_API'

# ATENÇÃO: Substitua pelos seus dados de autenticação do Discogs.
DISCOGS_USER_TOKEN = 'SEU_USER_TOKEN'

# Configuração dos clientes de API
musicbrainzngs.set_useragent("MediaTaggerPro", "0.1", "http://example.com")
discogs_client_instance = discogs_client.Client('MediaTaggerPro/0.1', user_token=DISCOGS_USER_TOKEN)

def lookup_fingerprint(filepath):
    """
    Busca os metadados de um arquivo no AcoustID usando fingerprinting.
    """
    try:
        results = acoustid.match(ACOUSTID_API_KEY, filepath)
        if not results:
            return None

        # Pega o primeiro resultado com a melhor pontuação
        best_result = results[0]
        score = best_result['score']
        recording_id = best_result['id']
        
        # Aqui, faríamos uma segunda chamada à API do MusicBrainz com o recording_id
        # para obter os metadados detalhados. Por enquanto, vamos retornar o ID.
        return {'recording_id': recording_id}

    except acoustid.NoBackendError:
        return None
    except acoustid.WebServiceError as e:
        return None
    except Exception as e:
        return None

def search_musicbrainz(artist, album, title):
    """
    Busca metadados no MusicBrainz usando as tags existentes.
    """
    try:
        # A busca pode ser mais refinada, mas vamos começar de forma simples
        result = musicbrainzngs.search_releases(artist=artist, release=album, limit=1)
        if result['release-list']:
            release = result['release-list'][0]
            return {
                'artist': release.get('artist-credit-phrase', ''),
                'album': release.get('title', ''),
                'date': release.get('date', '').split('-')[0],
            }
        return None
    except Exception as e:
        return None

def search_discogs_cover(artist, album):
    """
    Busca a capa de um álbum no Discogs.
    """
    try:
        results = discogs_client_instance.search(artist=artist, release_title=album, type='release')
        if results:
            # Pega a imagem principal do primeiro resultado
            main_image = results[0].images[0]['uri'] if results[0].images else None
            if main_image:
                return main_image
        return None
    except Exception as e:
        return None