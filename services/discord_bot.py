import discord
from discord.ext import commands, tasks
from config import Config

class DiscordNotifier:
    def __init__(self):
        self.bot = commands.Bot(
            command_prefix="!",
            intents=discord.Intents.default(),
            help_command=None
        )

    async def start_bot(self):
        await self.bot.start(Config.DISCORD_BOT_TOKEN)

    async def send_notification(self, channel_id, message):
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(message)