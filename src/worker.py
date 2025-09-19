import requests
from PyQt6.QtCore import QThread, pyqtSignal
from api_client import lookup_fingerprint, search_musicbrainz, search_discogs_cover
from metadata_reader import get_metadata
from metadata_writer import save_metadata

class MetadataWorker(QThread):
    """
    Worker thread para buscar metadados em segundo plano.
    """
    finished = pyqtSignal(int, dict)
    log_message = pyqtSignal(str)

    def __init__(self, row_index, filepath):
        super().__init__()
        self.row_index = row_index
        self.filepath = filepath

    def run(self):
        """
        Executa a tarefa em segundo plano.
        """
        self.log_message.emit(f"Iniciando busca de metadados para: {self.filepath}")
        
        # Estratégia de busca com fallback
        
        # 1. AcoustID (atualmente pausado)
        # metadata = lookup_fingerprint(self.filepath)
        
        # 2. MusicBrainz com tags existentes
        current_tags = get_metadata(self.filepath)
        if not current_tags:
            self.finished.emit(self.row_index, {})
            return

        metadata = search_musicbrainz(
            artist=current_tags.get('artist'),
            album=current_tags.get('album'),
            title=current_tags.get('title')
        )
        
        if metadata:
            # 3. Discogs para a capa do álbum
            cover_url = search_discogs_cover(
                artist=metadata.get('artist'),
                album=metadata.get('album')
            )
            if cover_url:
                try:
                    response = requests.get(cover_url)
                    response.raise_for_status()
                    metadata['cover_image_data'] = response.content
                except requests.RequestException as e:
                    self.log_message.emit(f"Erro ao baixar a capa: {e}")
        else:
            metadata = {}

        self.finished.emit(self.row_index, metadata)
        self.log_message.emit(f"Busca de metadados finalizada para: {self.filepath}")


class SaveWorker(QThread):
    """
    Worker thread para salvar metadados em segundo plano.
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    log_message = pyqtSignal(str)

    def __init__(self, files_to_save):
        super().__init__()
        self.files_to_save = files_to_save

    def run(self):
        total_files = len(self.files_to_save)
        for i, file_data in enumerate(self.files_to_save):
            success = save_metadata(
                filepath=file_data['filepath'],
                new_tags=file_data['new_tags'],
                cover_image_data=file_data.get('cover_image_data')
            )
            if success:
                self.log_message.emit(f"Metadados salvos com sucesso para {file_data['filepath']}")
            else:
                self.log_message.emit(f"Erro ao salvar metadados para {file_data['filepath']}")
            self.progress.emit(int(((i + 1) / total_files) * 100))
        
        self.finished.emit()