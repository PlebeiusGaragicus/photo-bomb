"""
API Settings dialog for configuring endpoint connection.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt


class APISettingsDialog(QDialog):
    """Dialog for configuring OpenAI-compatible API endpoint settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Settings")
        self.resize(500, 400)
        
        # Store the current config (will be modified if user saves)
        self.endpoint_url = ""
        self.api_key = ""
        self.model_name = ""
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Endpoint URL
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("Endpoint URL:")
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("https://api.openai.com/v1")
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.endpoint_input)
        layout.addLayout(endpoint_layout)
        
        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-...")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.key_input)
        layout.addLayout(key_layout)
        
        # Model Name
        model_layout = QHBoxLayout()
        model_label = QLabel("Model Name:")
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4o, claude-3-opus, etc.")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)
        
        # Test Connection
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self._test_connection)
        layout.addWidget(test_button)
        
        # Status area
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(80)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def _test_connection(self):
        """Test the API connection with current settings."""
        endpoint = self.endpoint_input.text().strip()
        api_key = self.key_input.text().strip()
        model = self.model_input.text().strip()
        
        if not endpoint:
            self.status_text.setText("Error: Endpoint URL is required")
            return
        
        # Import here to avoid circular dependency
        from src.core.api_client import VisionAPIClient
        
        client = VisionAPIClient()
        client.configure(endpoint, api_key, model)
        
        success, message = client.check_connection()
        
        if success:
            self.status_text.setText(f"✓ {message}")
        else:
            self.status_text.setText(f"✗ {message}")
    
    def _save_settings(self):
        """Save the configured settings."""
        endpoint = self.endpoint_input.text().strip()
        api_key = self.key_input.text().strip()
        model = self.model_input.text().strip()
        
        # Basic validation
        if not endpoint:
            QMessageBox.warning(self, "Validation Error", 
                              "Endpoint URL is required")
            return
        
        # Store values
        self.endpoint_url = endpoint
        self.api_key = api_key
        self.model_name = model
        
        self.accept()
    
    def load_settings(self, config):
        """Load settings from configuration."""
        self.endpoint_input.setText(config.get("api_endpoint", ""))
        self.key_input.setText(config.get("api_key", ""))
        self.model_input.setText(config.get("model_name", ""))
    
    def save_to_config(self, config):
        """Save current values to configuration object."""
        config.update({
            "api_endpoint": self.endpoint_url,
            "api_key": self.api_key,
            "model_name": self.model_name
        })
