import requests
from config import Config


class SteamAPI:
    @staticmethod
    def get_game_info(game_identifier):
        url = f"http://store.steampowered.com/api/appdetails?appids={game_identifier}"
        params = {"key": Config.STEAM_API_KEY}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data[str(game_identifier)]["success"]:
                return data[str(game_identifier)]["data"]
            return None
        except Exception as e:
            print(f"Steam API Error: {e}")
            return None

    @staticmethod
    def get_current_price(game_data):
        if "price_overview" in game_data:
            return game_data["price_overview"]["final"] / 100
        return None