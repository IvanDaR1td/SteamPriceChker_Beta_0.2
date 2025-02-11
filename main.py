import sys
import asyncio
from PySide6.QtWidgets import QApplication
from config import Config
from services.discord_bot import DiscordNotifier
from gui.main_window import MainWindow


async def run_app():
    app = QApplication(sys.argv)

    # 初始化 Discord 通知服务
    notifier = DiscordNotifier()
    asyncio.create_task(notifier.start_bot())

    # 创建主窗口
    window = MainWindow(notifier)
    window.show()

    # 运行 Qt 事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    asyncio.run(run_app())