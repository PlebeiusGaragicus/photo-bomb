"""
Batch processing dialog for photo analysis.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class AnalysisWorker(QThread):
    """Background thread for photo analysis."""
    
    progress = pyqtSignal(int)  # current_progress
    complete = pyqtSignal(list)  # results
    
    def __init__(self, photo_data_list, api_client):
        super().__init__()
        self.photo_data_list = photo_data_list
        self.api_client = api_client
        self.results = []
    
    def run(self):
        """Run the analysis in background thread."""
        total = len(self.photo_data_list)
        
        for i, (photo_id, photo_data) in enumerate(self.photo_data_list):
            try:
                result = self.api_client.analyze_photo(photo_data)
                self.results.append({"photo_id": photo_id, "results": result})
                self.progress.emit(int((i + 1) / total * 100))
            except Exception as e:
                self.results.append({
                    "photo_id": photo_id,
                    "error": str(e)
                })
        
        self.complete.emit(self.results)


class BatchAnalysisDialog(QDialog):
    """Dialog for analyzing photos with progress tracking."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Photo Analysis")
        self.resize(600, 500)
        self.worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Analyzing photos with vision model...")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to analyze...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Results list
        results_label = QLabel("Analysis Results:")
        layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self._cancel_analysis)
        layout.addWidget(cancel_button)
    
    def start_analysis(self, photo_data_list, api_client):
        """
        Start analyzing a batch of photos.
        
        Args:
            photo_data_list: List of (photo_id, photo_bytes) tuples
            api_client: Configured VisionAPIClient instance
        """
        self.worker = AnalysisWorker(photo_data_list, api_client)
        self.worker.progress.connect(self._on_progress)
        self.worker.complete.connect(self._on_complete)
        
        self.status_label.setText("Starting analysis...")
        self.results_list.clear()
        
        self.worker.start()
    
    def _on_progress(self, value):
        """Handle progress update from worker."""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Analyzing... {value}%")
    
    def _on_complete(self, results):
        """Handle analysis completion."""
        for result in results:
            photo_id = result.get("photo_id")
            
            if "error" in result:
                item_text = f"{photo_id}: ERROR - {result['error']}"
            else:
                # Format the result
                analysis = result.get("results", [{}])[0]
                category = analysis.get("category", "unknown")
                confidence = analysis.get("confidence", 0)
                
                item_text = f"{photo_id}: {category} ({confidence:.1%})"
            
            item = QListWidgetItem(item_text)
            self.results_list.addItem(item)
        
        self.status_label.setText(f"Analysis complete: {len(results)} photos processed")
    
    def _cancel_analysis(self):
        """Cancel the analysis."""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
        self.accept()
