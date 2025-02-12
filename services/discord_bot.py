import asyncio
import discord
import time
from discord.ext import commands
from config import Config

class DiscordNotifier:
    def __init__(self):
        """Initialize the Discord bot."""
        self.bot_ready = asyncio.Event()  # ✅ Use asyncio.Event() for safe readiness check
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True

        self.bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

        @self.bot.event
        async def on_ready():
            """Event triggered when the bot is ready."""
            print(f"🟢 [{time.strftime('%H:%M:%S')}] Bot is online: {self.bot.user}")
            self.bot_ready.set()  # ✅ Mark bot as ready using asyncio.Event()

    async def start_bot(self):
        """Starts the bot asynchronously inside the existing event loop."""
        try:
            print(f"🚀 [{time.strftime('%H:%M:%S')}] Starting Discord bot...")
            await self.bot.start(Config.DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            print(f"❌ [{time.strftime('%H:%M:%S')}] ERROR: Invalid Discord bot token!")
        except Exception as e:
            print(f"❌ [{time.strftime('%H:%M:%S')}] Bot startup failed: {str(e)}")

    async def send_notification(self, channel_id, message):
        """Send a message to a Discord channel safely within the bot event loop."""
        await self.bot_ready.wait()  # ✅ Wait until bot is fully ready

        print(f"📢 [{time.strftime('%H:%M:%S')}] Attempting to send message: {message}")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            print(f"❌ [{time.strftime('%H:%M:%S')}] ERROR: Channel {channel_id} not found! Check bot permissions.")
            return

        try:
            print(f"📤 [{time.strftime('%H:%M:%S')}] Sending message to {channel.name} (ID: {channel.id})...")
            await channel.send(message)
            print(f"✅ [{time.strftime('%H:%M:%S')}] SUCCESS: Message sent.")
        except discord.Forbidden:
            print(f"❌ [{time.strftime('%H:%M:%S')}] ERROR: Missing permissions to send messages in {channel.name}")
        except discord.HTTPException as e:
            print(f"❌ [{time.strftime('%H:%M:%S')}] ERROR: Discord API error: {e}")

    def notify(self, channel_id, message):
        """Ensure messages are sent inside the correct event loop."""
        asyncio.run_coroutine_threadsafe(self.send_notification(channel_id, message), self.bot.loop)

    async def stop_bot(self):
        """Safely stops the bot and closes the client session."""
        if self.bot.is_closed():
            print("⚠️ Bot is already stopped.")
            return

        print(f"🛑 [{time.strftime('%H:%M:%S')}] Attempting to stop bot...")

        try:
            await self.bot.close()  # ✅ Properly close the bot
            print(f"✅ [{time.strftime('%H:%M:%S')}] SUCCESS: Bot has been stopped.")
        except Exception as e:
            print(f"❌ [{time.strftime('%H:%M:%S')}] ERROR: Failed to stop the bot: {str(e)}")
