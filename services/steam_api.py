import aiohttp

class SteamAPI:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.base_url = "https://store.steampowered.com/api"

    async def search_game(self, query):
        """搜索Steam游戏"""
        params = {
            "term": query,
            "cc": "us",
            "l": "english",
            "fuzzy": 1
        }
        async with self.session.get(
            f"{self.base_url}/storesearch",
            params=params
        ) as response:
            data = await response.json()
            if data.get("items"):
                return {
                    "name": data["items"][0]["name"],
                    "id": data["items"][0]["id"]
                }
            return None

    async def get_price(self, appid):
        """获取游戏价格"""
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