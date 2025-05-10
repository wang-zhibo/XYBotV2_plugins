import tomllib

import aiohttp
from loguru import logger

from WechatAPI import WechatAPIClient
from utils.decorators import *
from utils.plugin_base import PluginBase


BASE_URL_VVHAN = "https://api.vvhan.com/api/"
BASE_URL_ALAPI = "https://v2.alapi.cn/api/"


class Apilot(PluginBase):
    description = "早报插件"
    author = "zhibo.wang"
    version = "1.0.0"


    def __init__(self):
        super().__init__()

        with open("plugins/Apilot/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)

        config = plugin_config["Apilot"]

        self.enable = config["enable"]
        self.command = config["command"]
        self.chatroom_list = config["chatroom_list"]
        self.alapi_token = config["alapi_token"]
        self.session = None

    async def initialize(self):
        """初始化 aiohttp 会话"""
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        """清理 aiohttp 会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        if not self.enable:
            return

        content = str(message["Content"]).strip()
        command = content.split(" ")

        logger.info(f"[Apilot] 收到消息: {command}")
        if not len(command) or command[0] not in self.command:
            return

        sender_wxid = message["SenderWxid"]
        logger.info(f" sender_wxid: {sender_wxid}")

        # 确保 session 已初始化
        if self.session is None or self.session.closed:
            await self.initialize()

        # 获取早报信息
        morning_news = await self.get_morning_news()
        logger.info(f" morning_news: {morning_news}")
        if morning_news is None:
            return
        a, b, c = await bot.send_text_message(message["FromWxid"], morning_news)


    @schedule('cron', hour=8, minute=30, second=30)
    async def daily_task_news(self, bot: WechatAPIClient):
       # 每天早上8:30执行 发送早报
        if not self.enable:
            return
        # 确保 session 已初始化
        if self.session is None or self.session.closed:
            await self.initialize()
        # 获取早报信息
        morning_news = await self.get_morning_news()
        if morning_news is None:
            return
        for chatroom_info in self.chatroom_list:
            FromWxid, FromWxName = chatroom_info.split("|")
            # 发送早报信息
            await bot.send_text_message(FromWxid, morning_news)
            await asyncio.sleep(3)


    async def get_morning_news(self):
        # 早报
        if not self.alapi_token:
            url = BASE_URL_VVHAN + "60s?type=json"
            payload = "format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            try:
                morning_news_info = await self.make_request(url, method="POST", headers=headers, data=payload)
                if isinstance(morning_news_info, dict) and morning_news_info.get('success'):
                    # 提取并格式化新闻
                    news_list = ["{}. {}".format(idx, news) for idx, news in enumerate(morning_news_info["data"][:-1], 1)]
                    formatted_news = f"☕ {morning_news_info['data']['date']}  今日早报\n"
                    formatted_news = formatted_news + "\n".join(news_list)
                    weiyu = morning_news_info["data"][-1].strip()
                    return f"{formatted_news}\n\n{weiyu}\n"
                else:
                    return None
            except Exception as e:
                logger.error(f"早报获取失败: {e}")
        else:
            url = BASE_URL_ALAPI + "zaobao"
            payload = f"token={self.alapi_token}&format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            try:
                morning_news_info = await self.make_request(url, method="POST", headers=headers, data=payload)
                if isinstance(morning_news_info, dict) and morning_news_info.get('code') == 200:
                    img_url = morning_news_info['data']['image']
                    news_list = morning_news_info['data']['news']
                    weiyu = morning_news_info['data']['weiyu']

                    # 整理新闻为有序列表
                    formatted_news = f"☕ {morning_news_info['data']['date']}  今日早报\n"
                    formatted_news = formatted_news + "\n".join(news_list)
                    # 组合新闻和微语
                    return f"{formatted_news}\n\n{weiyu}\n"
                else:
                    return None
            except Exception as e:
                logger.error(f"早报获取失败: {e}")


    async def make_request(self, url, method="GET", headers=None, params=None, data=None, json_data=None):
        """使用 aiohttp 发送异步请求"""
        try:
            if self.session is None or self.session.closed:
                await self.initialize()
                
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers, params=params) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, headers=headers, data=data, json=json_data) as response:
                    return await response.json()
            else:
                return {"success": False, "message": "不支持的 HTTP 方法"}
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return {"success": False, "message": f"请求失败: {str(e)}"}

