"""Configuration centrale de DocFlow"""
import os

class Config:
    APP_NAME = "DocFlow"
    APP_VERSION = "1.0.0"
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docflow.db")
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    MAX_FILE_SIZE_MB = 50
    SUPPORTED_INPUTS = [".xlsx", ".xls", ".csv"]
    SUPPORTED_OUTPUTS = ["xlsx", "pdf", "docx", "csv"]
    CHART_THEME = "plotly_dark"
    CHART_COLORS = ["#e94560", "#f5a623", "#2ecc71", "#3498db", "#9b59b6", "#1abc9c"]

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.UPLOAD_DIR, cls.OUTPUT_DIR, cls.REPORTS_DIR]:
            os.makedirs(d, exist_ok=True)

Config.ensure_dirs()
