import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

rich_menu_list = line_bot_api.get_rich_menu_list()

try:
    rich_menu_list = line_bot_api.get_rich_menu_list()
    if not rich_menu_list:
        print("No rich menu found")
    else:
        for rich_menu in rich_menu_list:
            line_bot_api.delete_rich_menu(rich_menu.rich_menu_id)
        print("All rich menus have been deleted successfully.")
except LineBotApiError as e:
    print(f"Error occurred: {e.message}")
