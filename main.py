import sys
import asyncio
import qasync
from PySide6.QtWidgets import QApplication
from services.discord_bot import DiscordNotifier
from gui.main_window import MainWindow


async def main():
    # ✅ Ensure QApplication is created only once
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    notifier = DiscordNotifier()

    # ✅ Start Qt event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # ✅ Create GUI with the correct notifier
    print("🛠️ Creating MainWindow...")
    try:
        window = MainWindow(notifier)  # ✅ Pass the bot notifier correctly
        window.show()
        print("✅ MainWindow should now be visible.")
    except Exception as e:
        print(f"❌ ERROR: Failed to create MainWindow - {str(e)}")
        return

    try:
        await notifier.start_bot()  # ✅ Properly await the bot startup
    except Exception as e:
        print(f"❌ Bot failed to start: {str(e)}")
        return  # Exit if the bot cannot start

    timeout = 15  # Prevent infinite waiting
    while not notifier.bot_ready and timeout > 0:
        print(f"⏳ Waiting for Discord bot to initialize... ({timeout}s left)")
        await asyncio.sleep(1)
        timeout -= 1

    if not notifier.bot_ready:
        print("❌ Bot failed to initialize within timeout!")
        return  # Exit if the bot is not ready

    # ✅ Keep Qt running
    await qasync.async_()  # ✅ This properly starts the GUI event loop


if __name__ == "__main__":
    app = QApplication(sys.argv)  # ✅ Ensure QApplication exists

    try:
        qasync.run(main())  # ✅ Correctly integrate Qt and asyncio
    except Exception as e:
        print(f"❌ Critical error in main loop: {str(e)}")
