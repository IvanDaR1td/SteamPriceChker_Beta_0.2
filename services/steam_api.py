import aiohttp

class SteamAPI:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.base_url = "https://store.steampowered.com/api"

    async def search_game(self, query):
        """Search Steam games and return multiple results"""
        params = {
            "term": query,
            "cc": "us",
            "l": "english",
            "fuzzy": 1
        }
        async with self.session.get(f"{self.base_url}/storesearch", params=params) as response:
            data = await response.json()
            print("Steam API Response:", data)  # Debugging
            if data.get("items"):
                return [{"name": item["name"], "id": item["id"]} for item in data["items"]]
            return []

    async def get_price(self, appid):
        """get game price"""
        params = {
            "appids": appid,
            "cc": "us",
            "filters": "price_overview"
        }
        async with self.session.get(
            f"{self.base_url}/appdetails",
            params=params
        ) as response:
            data = await response.json()
            if data and data.get(str(appid), {}).get("data", {}).get("price_overview"):
                return data[str(appid)]["data"]["price_overview"]["final"] / 100
            return None
