def apply_dark_theme(window):
    window.setStyleSheet("""
        QWidget {
            background-color: #2D2D2D;
            color: #FFFFFF;
        }
        QLineEdit {
            background-color: #404040;
            border: 1px solid #606060;
        }
        QListWidget {
            background-color: #404040;
        }
    """)