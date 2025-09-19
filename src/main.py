import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from ui_main_window import Ui_MainWindow
from metadata_reader import get_metadata
from worker import MetadataWorker, SaveWorker

class MediaTaggerPro(QMainWindow, Ui_MainWindow):
    log_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.workers = []
        self.current_cover_data = None
        self.setup_table_model()
        self.connect_signals()
        self.log_message.connect(self.logOutput.append)
        self.show()

    def setup_table_model(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            'Arquivo', 'Artista', 'Álbum', 'Título', 'Faixa', 'Ano',
            'Novo Artista', 'Novo Álbum', 'Novo Título', 'Nova Faixa', 'Novo Ano'
        ])
        self.tableView.setModel(self.model)

    def connect_signals(self):
        self.addFilesButton.clicked.connect(self.open_file_dialog)
        self.addFolderButton.clicked.connect(self.open_folder_dialog)
        self.saveButton.clicked.connect(self.save_changes)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos de Música",
            "",
            "Arquivos de Áudio (*.mp3 *.flac *.m4a *.wav)"
        )
        if files:
            self.add_files(files)

    def open_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta de Músicas"
        )
        if folder:
            filepaths = []
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')):
                        filepaths.append(os.path.join(root, file))
            self.add_files(filepaths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]
        self.add_files(paths)

    def add_files(self, filepaths):
        for path in filepaths:
            if os.path.isfile(path):
                metadata = get_metadata(path)
                if metadata:
                    row_index = self.model.rowCount()
                    row_items = [
                        QStandardItem(os.path.basename(path)),
                        QStandardItem(metadata.get('artist', '')),
                        QStandardItem(metadata.get('album', '')),
                        QStandardItem(metadata.get('title', '')),
                        QStandardItem(metadata.get('tracknumber', '')),
                        QStandardItem(metadata.get('date', ''))
                    ]
                    # Armazena o caminho completo do arquivo no primeiro item da linha
                    row_items[0].setData(path, Qt.ItemDataRole.UserRole)
                    
                    self.model.appendRow(row_items)
                    self.start_metadata_worker(row_index, path)

    def start_metadata_worker(self, row_index, filepath):
        worker = MetadataWorker(row_index, filepath)
        worker.finished.connect(self.update_metadata_in_table)
        worker.log_message.connect(self.log_message.emit)
        self.workers.append(worker)
        worker.start()

    def update_metadata_in_table(self, row_index, metadata):
        self.model.setItem(row_index, 6, QStandardItem(metadata.get('artist', '')))
        # Colunas "Depois"
        artist_item = QStandardItem(metadata.get('artist', ''))
        album_item = QStandardItem(metadata.get('album', ''))
        title_item = QStandardItem(metadata.get('title', ''))
        track_item = QStandardItem(metadata.get('tracknumber', ''))
        date_item = QStandardItem(metadata.get('date', ''))

        # Tornar as colunas "Depois" editáveis
        for item in [artist_item, album_item, title_item, track_item, date_item]:
            item.setEditable(True)

        self.model.setItem(row_index, 6, artist_item)
        self.model.setItem(row_index, 7, album_item)
        self.model.setItem(row_index, 8, title_item)
        self.model.setItem(row_index, 9, track_item)
        self.model.setItem(row_index, 10, date_item)

        if 'cover_image_data' in metadata:
            self.current_cover_data = metadata['cover_image_data']
            pixmap = QPixmap()
            pixmap.loadFromData(self.current_cover_data)
            self.coverLabel.setPixmap(pixmap.scaled(
                self.coverLabel.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.current_cover_data = None
            self.coverLabel.setText("Capa não encontrada")

    def save_changes(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if not selected_indexes:
            self.log_message.emit("Nenhum arquivo selecionado para salvar.")
            return

        files_to_save = []
        for index in selected_indexes:
            row = index.row()
            
            filepath = self.model.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if not filepath:
                continue

            new_tags = {
                'artist': self.model.item(row, 6).text(),
                'album': self.model.item(row, 7).text(),
                'title': self.model.item(row, 8).text(),
                'tracknumber': self.model.item(row, 9).text(),
                'date': self.model.item(row, 10).text(),
            }
            
            files_to_save.append({
                'filepath': filepath,
                'new_tags': new_tags,
                'cover_image_data': self.current_cover_data
            })

        self.save_worker = SaveWorker(files_to_save)
        self.save_worker.progress.connect(self.update_progress_bar)
        self.save_worker.finished.connect(self.on_save_finished)
        self.save_worker.log_message.connect(self.log_message.emit)
        self.save_worker.start()

    def update_progress_bar(self, value):
        self.progressBar.setValue(value)

    def on_save_finished(self):
        self.progressBar.setValue(0)
        self.log_message.emit("Processo de salvamento concluído.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MediaTaggerPro()
    sys.exit(app.exec())