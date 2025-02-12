import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QVBoxLayout,
    QWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from services.steam_api import SteamAPI
import aiohttp
from models import TrackedGame
from datetime import datetime
from config import Config


class MainWindow(QMainWindow):
    def __init__(self, notifier):
        super().__init__()
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
        self.search_input = QLineEdit(self)
        self.search_button = QPushButton("Search Game", self)
        self.search_button.clicked.connect(self.on_search)

        self.result_label = QLabel("Search Results:", self)
        self.result_table = QTableWidget(self)
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Game Name", "Game ID", "Price"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.track_button = QPushButton("Track Game", self)
        self.track_button.clicked.connect(self.on_track)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_table)
        layout.addWidget(self.track_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_search(self):
        """Handle search button click."""
        query = self.search_input.text()
        if query:
            asyncio.create_task(self.search_game(query))

    async def search_game(self, query):
        """Asynchronous search for a game."""
        try:
            async with aiohttp.ClientSession() as session:
                steam_api = SteamAPI(session)
                result = await steam_api.search_game(query)
                if result:
                    price = await steam_api.get_price(result["id"])
                    self.display_search_result(result["name"], result["id"], price)
                else:
                    print("Game not found")
        except Exception as e:
            print(f"Search error: {str(e)}")

    def display_search_result(self, name, appid, price):
        """Display the search results."""
        self.result_table.setRowCount(1)
        self.result_table.setItem(0, 0, QTableWidgetItem(name))
        self.result_table.setItem(0, 1, QTableWidgetItem(str(appid)))
        price_text = f"${price:.2f}" if price else "N/A"
        self.result_table.setItem(0, 2, QTableWidgetItem(price_text))

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
                    last_checked=datetime.now(),
                    channel_id=Config.DISCORD_CHANNEL_ID
                )
                self.tracked_games.append(new_game)
                print(f"Tracking game: {name}")

                # Use `asyncio.run_coroutine_threadsafe()` for safe async execution
                message = f"Tracking started: **{name}** (ID: {appid}) Price: ${price:.2f}"
                asyncio.run_coroutine_threadsafe(
                    self.notifier.send_notification(int(Config.DISCORD_CHANNEL_ID), message),
                    self.notifier.bot.loop
                )

            except Exception as e:
                print(f"Tracking error: {str(e)}")

    async def check_price_changes(self):
        """Background price check task."""
        try:
            while True:
                print(" Checking for price changes...")
                for game in self.tracked_games.copy():
                    try:
                        async with aiohttp.ClientSession() as session:
                            steam_api = SteamAPI(session)
                            current_price = await steam_api.get_price(game.appid)
                            if current_price and current_price < game.initial_price:
                                discount = game.initial_price - current_price
                                discount_percent = (discount / game.initial_price) * 100
                                message = (
                                    f"🎮 **{game.name}** is on sale!\n"
                                    f"💰 Original price: ${game.initial_price:.2f}\n"
                                    f"🛒 Current price: ${current_price:.2f}\n"
                                    f"🎉 Discount: {discount_percent:.2f}%"
                                )
                                #  Add `await` here
                                await self.notifier.send_notification(game.channel_id, message)
                                game.initial_price = current_price  # Update baseline price
                    except Exception as e:
                        print(f"Price check failed: {game.name} - {str(e)}")
                await asyncio.sleep(3600)  # Check every hour
        except asyncio.CancelledError:
            print(" Price check task stopped")

