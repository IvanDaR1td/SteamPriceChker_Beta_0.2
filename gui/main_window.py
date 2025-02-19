import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QVBoxLayout,
    QWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import qtawesome as qta
from services.steam_api import SteamAPI
import aiohttp
from datetime import datetime
from config import Config


class TrackedGame:
    def __init__(self, appid, name, initial_price, region, last_checked, channel_id):
        self.appid = appid
        self.name = name
        self.initial_price = initial_price
        self.region = region
        self.last_checked = last_checked
        self.channel_id = channel_id


class MainWindow(QMainWindow):
    def __init__(self, notifier):
        super().__init__()

        self.regions = {
            "Europe (Ireland)": ("ie", "en"),
            "United States": ("us", "en"),
            "China": ("cn", "zh-CN"),
            "Japan": ("jp", "ja"),
            "Russia": ("ru", "ru")
        }
        self.current_region = "ie"
        self.current_language = "en"

        self.notifier = notifier
        self.tracked_games = []
        self.check_task = None

        self._init_ui()
        self.check_task = asyncio.create_task(self.check_price_changes())

    def closeEvent(self, event):
        """Cancel async tasks when the window is closed."""
        if self.check_task and not self.check_task.done():
            self.check_task.cancel()
        super().closeEvent(event)

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Steam Price Tracker")
        self.setGeometry(100, 100, 800, 600)

        # Search bar and button
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Enter game name...")
        self.search_button = QPushButton(self)
        self.search_button.setIcon(qta.icon("fa5s.search"))
        self.search_button.clicked.connect(self.on_search)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # Region combo box
        self.region_combo = QComboBox()
        for region in self.regions:
            self.region_combo.addItem(region)
        self.region_combo.currentTextChanged.connect(self.on_region_changed)

        # Result label and table
        self.result_label = QLabel("Search Results:", self)
        self.result_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.result_table = QTableWidget(self)
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Game Name", "Game ID", "Price"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Track button
        self.track_button = QPushButton(self)
        self.track_button.setIcon(qta.icon("fa5s.plus"))
        self.track_button.setText("Track Game")
        self.track_button.clicked.connect(self.on_track)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Region:"))
        layout.addWidget(self.region_combo)
        layout.addLayout(search_layout)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_table)
        layout.addWidget(self.track_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_region_changed(self, region_name):
        """Handle region selection change."""
        self.current_region, self.current_language = self.regions[region_name]

    def on_search(self):
        """Handle search button click."""
        query = self.search_input.text().strip()
        if query:
            asyncio.create_task(self.search_game(query))

    async def search_game(self, query):
        """Asynchronous search for multiple games."""
        try:
            async with aiohttp.ClientSession() as session:
                steam_api = SteamAPI(session)
                results = await steam_api.search_game(
                    query, region=self.current_region, language=self.current_language
                )

                self.result_table.setRowCount(0)

                if results:
                    self.result_table.setRowCount(len(results))
                    for row, result in enumerate(results):
                        price = await steam_api.get_price(result["id"])
                        await self.display_search_result(row, result["name"], result["id"], price)
                else:
                    print("No games found")
        except Exception as e:
            print(f"Search error: {str(e)}")

    async def get_price_for_display(self, appid):
        """Fetch and format price with currency symbol."""
        async with aiohttp.ClientSession() as session:
            steam_api = SteamAPI(session)
            price = await steam_api.get_price(appid, self.current_region)
            return await self.format_price(price, self.current_region)

    async def format_price(self, price, region):
        """Format price with correct currency symbol."""
        symbols = {
            "us": "$",
            "cn": "¥",
            "jp": "¥",
            "ie": "€",
            "ru": "₽"
        }
        symbol = symbols.get(region, "$")
        return f"{symbol}{price:.2f}" if price else "N/A"

    async def display_search_result(self, row, name, appid, price):
        """Display search results in the table."""
        formatted_price = await self.get_price_for_display(appid)
        self.result_table.setItem(row, 0, QTableWidgetItem(name))
        self.result_table.setItem(row, 1, QTableWidgetItem(str(appid)))
        self.result_table.setItem(row, 2, QTableWidgetItem(formatted_price))

    def on_track(self):
        """Handle the track game button click."""
        selected_row = self.result_table.currentRow()
        if selected_row >= 0:
            try:
                name = self.result_table.item(selected_row, 0).text()
                appid = int(self.result_table.item(selected_row, 1).text())
                price_text = self.result_table.item(selected_row, 2).text()

                if price_text == "N/A":
                    raise ValueError("Price not available")

                price = float(price_text.replace("$", ""))
                new_game = TrackedGame(
                    appid=appid,
                    name=name,
                    initial_price=price,
                    region=self.current_region,
                    last_checked=datetime.now(),
                    channel_id=Config.DISCORD_CHANNEL_ID
                )
                self.tracked_games.append(new_game)
                print(f"Tracking game: {name}")

                # Schedule notification in the bot's event loop
                message = f"Tracking started: **{name}** (ID: {appid}) Price: ${price:.2f}"
                asyncio.ensure_future(self.notifier.send_notification(int(Config.DISCORD_CHANNEL_ID), message))

            except Exception as e:
                print(f"Tracking error: {str(e)}")

    async def check_price_changes(self):
        """Background task to check for price changes."""
        try:
            while True:
                print("Checking for price changes...")
                for game in self.tracked_games.copy():
                    try:
                        async with aiohttp.ClientSession() as session:
                            steam_api = SteamAPI(session)
                            current_price = await steam_api.get_price(game.appid, game.region)
                            if current_price and current_price < game.initial_price:
                                message = f"🎮 **{game.name}** is now ${current_price:.2f}!"
                                await self.notifier.send_notification(game.channel_id, message)
                                game.initial_price = current_price
                    except Exception as e:
                        print(f"Price check failed for {game.name}: {str(e)}")
                await asyncio.sleep(3600)  # Check every hour
        except asyncio.CancelledError:
            print("Price check task stopped")
