import asyncio
import json
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLineEdit, QPushButton, QListWidget,
                               QCheckBox, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from aiohttp import ClientSession
from services.steam_api import SteamAPI
from gui.themes import apply_dark_theme
from config import Config

class MainWindow(QMainWindow):
    def __init__(self, discord_notifier):
        super().__init__()
        self.discord_notifier = discord_notifier
        self.tracked_games = []
        self.client_session = ClientSession()
        self.init_ui()
        self.load_tracked_games()
        self.setup_price_checker()

    async def closeEvent(self, event):
        await self.client_session.close()  # Ensure session is closed properly
        event.accept()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(lambda: asyncio.create_task(self.handle_search()))

        self.tracked_list = QListWidget()
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_theme)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_game)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.remove_button)

        layout.addWidget(self.search_input)
        layout.addLayout(button_layout)
        layout.addWidget(self.tracked_list)
        layout.addWidget(self.dark_mode_checkbox)

        self.central_widget.setLayout(layout)
        self.setWindowTitle("Steam Price Tracker")
        self.resize(800, 600)

    def toggle_theme(self, state):
        apply_dark_theme(self) if state == Qt.Checked else self.setStyleSheet("")

    async def handle_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Input Error", "Please enter a game name.")
            return

        try:
            steam_api = SteamAPI(self.client_session)
            game_data = await steam_api.search_game(query)
            if game_data:
                QMessageBox.information(self, "Search Success", f"Found game: {game_data['name']}")
                self.tracked_games.append(game_data)
                self.tracked_list.addItem(game_data['name'])
                self.save_tracked_games()
            else:
                QMessageBox.warning(self, "Not Found", "No game found with that name.")
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Error fetching game data: {str(e)}")

    def setup_price_checker(self):
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(lambda: asyncio.create_task(self.check_prices()))
        self.check_timer.start(Config.CHECK_INTERVAL * 1000)

    async def check_prices(self):
        for game in self.tracked_games:
            try:
                steam_api = SteamAPI(self.client_session)
                updated_price = await steam_api.get_price(game['id'])
                if updated_price and updated_price != game['price']:
                    game['price'] = updated_price
                    self.discord_notifier.notify_price_drop(game['name'], updated_price)
            except Exception as e:
                print(f"Error checking price for {game['name']}: {e}")

    def load_tracked_games(self):
        try:
            with open("tracked_games.json", "r") as file:
                self.tracked_games = json.load(file)
                for game in self.tracked_games:
                    self.tracked_list.addItem(game['name'])
        except (FileNotFoundError, json.JSONDecodeError):
            self.tracked_games = []

    def save_tracked_games(self):
        with open("tracked_games.json", "w") as file:
            json.dump(self.tracked_games, file, indent=4)

    def remove_selected_game(self):
        selected_item = self.tracked_list.currentItem()
        if selected_item:
            game_name = selected_item.text()
            self.tracked_list.takeItem(self.tracked_list.row(selected_item))
            self.tracked_games = [game for game in self.tracked_games if game['name'] != game_name]
            self.save_tracked_games()
