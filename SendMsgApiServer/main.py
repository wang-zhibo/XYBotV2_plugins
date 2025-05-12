import asyncio
import tomllib
from datetime import datetime

import os
import json 
import time
import aiohttp
import aiofiles
from loguru import logger
from tabulate import tabulate

from WechatAPI import WechatAPIClient
from utils.decorators import *
from utils.plugin_base import PluginBase
from plugins.SendMsgApiServer.file_api import FileWriter



class SendMsgApiServer(PluginBase):
    description = "api 发送消息"
    author = "zhibo.wang"
    version = "1.0.0"

    def __init__(self):
        tag = "SendMsgApiServer"
        super().__init__()

        try:

            with open("plugins/SendMsgApiServer/config.toml", "rb") as f:
                plugin_config = tomllib.load(f)

            with open("main_config.toml", "rb") as f:
                main_config = tomllib.load(f)

            config = plugin_config["SendMsgApiServer"]
            main_config = main_config["XYBot"]

            self.enable = config["enable"]
            self.command = config["command"]

            self.admins = main_config["admins"]

            # 文件路径和目录
            curdir = os.path.dirname(__file__)

            self.friend_list_file = os.path.join(curdir, "contact_friend.json")
            self.chatroom_list_file = os.path.join(curdir, "contact_room.json")

            self.file_path = os.path.join(curdir, "data.json")
            # 启动文件写入的 API 服务
            FileWriter()
            logger.info(f"[{tag}] inited")
        except Exception as e:
            log_msg = f"{tag}: init failed error: {e}"
            logger.error(log_msg)
        

    @schedule('interval', seconds=9)
    async def handle_message(self, bot: WechatAPIClient):
        """
        每九秒 读取内容并发送消息
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data_str = file.read().strip()
                if not data_str:
                    return
                data_list = json.loads(data_str)

            # 批量发送完后，清空文件
            for record in data_list:
                await self.process_message(bot, record)
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write('')

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"读取文件 {self.file_path} 出错: {e}")


    async def process_message(self, bot, data):
        """
        读取 data.json 中的一条数据并发送
        """
        try:
            receiver_names = data["receiver_name"]  # 可能是字符串或者列表
            content = data["message"]
            group_names = data["group_name"]  # 同样可能是字符串或者列表
            await self.send_message(bot, receiver_names, content, group_names)
        except Exception as e:
            logger.error(f"处理消息时发生异常: {e}")


    async def send_message(self, bot, receiver_names, content, group_names):
        """
        :param receiver_names: list[str] 接收者名称列表（可能包含 "所有人"）
        :param content: str 消息内容
        :param group_names: list[str] 群聊名称列表
        """
        # 保证都是 list
        if isinstance(receiver_names, str):
            receiver_names = [receiver_names]
        if isinstance(group_names, str):
            group_names = [group_names]

        group_names = group_names or []

        logger.info(f"receiver_names: {receiver_names}, content: {content}, group_names: {group_names}")
        try:
            # 由于这是实例方法，我们需要从类的属性中获取 bot 实例
            await self._send_hhhhh_message(bot, receiver_names, content, group_names)
        except Exception as e:
            logger.error(f"发送消息时发生异常: {e}")
            raise e


    async def _send_hhhhh_message(self, bot: WechatAPIClient, receiver_names, content, group_names):
        """
        """
        # 如果有群
        if group_names:
            await self._send_hhhhh_group_message(bot, receiver_names, content, group_names)
        else:
            # 否则发给好友
            await self._send_hhhhh_friend_message(bot, receiver_names, content)


    async def _send_hhhhh_group_message(self, bot: WechatAPIClient, receiver_names, content, group_names):
        # 读取本地缓存的群通讯录
        if not os.path.exists(self.chatroom_list_file):
            logger.info("群通讯录文件不存在，请先执行'更新群成员'")
            return

        chatroom_list = json.load(open(self.chatroom_list_file, 'r', encoding='utf-8'))
        # 匹配群聊
        chatroom_infos = []
        for group_name in group_names:
            for chatroom_info in chatroom_list:
                chatroom_name = chatroom_info.get("chatroomName")
                logger.info(f"匹配群名: {group_name}, {chatroom_name}")
                if group_name == chatroom_name:
                    chatroom_infos.append(chatroom_info)
                    break

        logger.info(f"过滤群结果: {chatroom_infos}")
        if not chatroom_infos:
            logger.info("没有找到对应的群聊")
            return

        # 针对每个群聊发送消息
        for chatroom_info in chatroom_infos:
            to_room_id = chatroom_info.get("chatroomId")
            chatroom_name = chatroom_info.get("chatroomName")

            if not receiver_names or receiver_names == ["所有人"]:
                # @所有人
                content_at = "@所有人\u2005 " if receiver_names == ["所有人"] else ""
                final_content = f"{content_at}{content}"
                await bot.send_text_message(to_room_id, final_content)
            else:
                members = chatroom_info.get("memberList", [])
                content_at = ""
                ats = []
                logger.info(f"receiver_names: {receiver_names}")
                if len(chatroom_infos) > 0 and len(receiver_names) > 0:
                    logger.info("消息")
                    # 拼装 相关消息
                    for receiver_name in receiver_names:
                        for mem in members:
                            if mem.get("nickName") == receiver_name:
                                wxid = mem.get("wxid")
                                content_at += f"@{receiver_name}\u2005" if receiver_name else ""
                                ats.append(wxid)
                if len(receiver_names) > 0:
                    logger.info("艾特人消息")
                    if content_at and ats:
                        final_content = f"{content_at} {content}"
                        logger.info(f"手动发送微信群聊消息成功, 发送群聊:{chatroom_name}, 接收者:{ats}, 消息内容：{final_content}")
                        await bot.send_text_message(to_room_id, final_content, ats)
                    else:
                        logger.info(f"未找到群成员")
                else:
                    logger.info("不艾特人消息")
                    final_content = f"{content}"
                    logger.info(f"手动发送微信群聊消息成功, 发送群聊:{chatroom_name}, 接收者:{ats}, 消息内容：{final_content}")
                    await bot.send_text_message(to_room_id, final_content)
            await asyncio.sleep(0.9)


    async def _send_hhhhh_friend_message(self, bot: WechatAPIClient, receiver_names, content):
        if not os.path.exists(self.friend_list_file):
            logger.info("好友通讯录文件不存在，请先执行\"更新好友列表\"")
            return

        friend_list = json.load(open(self.friend_list_file, 'r', encoding='utf-8'))
        # 匹配好友
        friend_infos = []
        for receiver_name in receiver_names:
            for friend_info in friend_list:
                if receiver_name in (friend_info.get("nickName")):
                    friend_infos.append(friend_info)
                    break

        if not friend_infos:
            logger.info("未找到对应好友")
            return 

        for friend_info in friend_infos:
            to_friend_id = friend_info.get("userName")
            nickName = friend_info.get("nickName")
            logger.info(f"手动发送微信消息成功, 发送人:{nickName} 消息内容：{content}")
            await bot.send_text_message(to_friend_id, content)
            await asyncio.sleep(0.9)


    @schedule('cron', hour=5, minute=30, second=30)
    async def daily_task_update_ontacts(self, bot: WechatAPIClient):
       # 每天早上5:30执行 更新通讯录列表
        if not self.enable:
            return
        logger.info("定时任务测试, 我每天早上5点30分30秒执行")
        if len(self.admins) > 0:
            await self.fetch_contacts_info(bot, self.admins[0])


    async def fetch_contacts_info(self, bot, FromWxid):
        """
        获取并处理微信通讯录信息
        
        Args:
            bot: WechatAPIClient实例
            
        Returns:
            tuple[list, list]: 返回(好友列表, 群聊列表)的元组
        """
        start_time = datetime.now()
        logger.info("开始获取通讯录信息时间：{}", start_time)

        id_list = []
        wx_seq, chatroom_seq = 0, 0
        while True:
            contact_list = await bot.get_contract_list(wx_seq, chatroom_seq)
            id_list.extend(contact_list["ContactUsernameList"])
            wx_seq = contact_list["CurrentWxcontactSeq"]
            chatroom_seq = contact_list["CurrentChatRoomContactSeq"]
            if contact_list["CountinueFlag"] != 1:
                break
            await asyncio.sleep(3)

        get_list_time = datetime.now()
        logger.info("获取通讯录信息列表耗时：{}", get_list_time - start_time)

        # 使用协程池处理联系人信息获取
        info_list = []

        async def fetch_contacts(id_chunk):
            contact_info = await bot.get_contact(id_chunk)
            return contact_info

        # 过滤掉系统账号
        remove_list = ['weixin', 'fmessage', 'medianote', 'floatbottle']
        filtered_id_list = [item for item in id_list if item not in remove_list]
        
        chunks = [filtered_id_list[i:i + 20] for i in range(0, len(filtered_id_list), 20)]
        logger.info(f"chunks: {chunks}")

        sem = asyncio.Semaphore(20)

        async def worker(chunk):
            async with sem:
                logger.info(f"chunk111: {chunk}")
                return await fetch_contacts(chunk)

        tasks = [worker(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        # 合并结果
        for result in results:
            info_list.extend(result)

        done_time = datetime.now()
        logger.info("获取通讯录详细信息耗时：{}", done_time - get_list_time)
        logger.info("获取通讯录信息总耗时：{}", done_time - start_time)
        info_list_b = json.dumps(info_list, ensure_ascii=False)

        logger.info(f"通讯录: info_list count : {len(info_list)}, {type(info_list)}")

        chatroom_list = []
        friend_list = []

        for info in info_list:
            try:
                if isinstance(info, dict):
                    UserName = info.get("UserName", {}).get("string", "")
                    NickName = info.get("NickName", {}).get("string", "")
                    VerifyInfo = info.get("VerifyInfo", None)

                    if UserName:
                        b = json.dumps(info, ensure_ascii=False)
                        logger.info(f"通讯录: info: {b}")
                        logger.info("\n***********************************\n")
                        if "@chatroom" in UserName:
                            # 群
                            data_info = {
                                "chatroomId": UserName,
                                "chatroomName": NickName
                            }
                            memberList = []
                            ChatRoomMember = info.get("NewChatroomData").get("ChatRoomMember")
                            for ChatRoomMember_ in ChatRoomMember:
                                member_info = {
                                    "wxid": ChatRoomMember_.get("UserName"),
                                    "nickName": ChatRoomMember_.get("NickName")
                                }
                                memberList.append(member_info)
                            chatroom_info = data_info | {"memberList": memberList}
                            chatroom_list.append(chatroom_info)
                        elif "@chatroom" not in UserName and VerifyInfo is None:
                            # 好友
                            data_info = {
                                "userName": UserName,
                                "nickName": NickName
                            }
                            friend_list.append(data_info)
            except Exception as e:
                logger.error(f"处理联系人信息时发生异常: {e}, {info}")
                continue
        
        msg = f"获取完成，好友数量: {len(friend_list)}, 群聊数量: {len(chatroom_list)}"
        logger.info(msg)
        await self.save_contact_friends(friend_list)
        await self.save_contact_rooms(chatroom_list)
        if FromWxid:
            a, b, c = await bot.send_text_message(FromWxid, msg)
        return


    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        
        if not self.enable:
            return

        content = str(message["Content"]).strip()
        command = content.split(" ")

        if not len(command) or command[0] not in self.command:
            return

        sender_wxid = message["SenderWxid"]
        
        if sender_wxid not in self.admins:
            await bot.send_text_message(message["FromWxid"], "❌你配用这个指令吗？😡")
            return
        a, b, c = await bot.send_text_message(message["FromWxid"], "正在获取通讯录信息，请稍等...")
        await self.fetch_contacts_info(bot, message["FromWxid"])


    async def save_contact_friends(self, friend_list):
        try:
            logger.info(f"准备保存好友列表，共 {len(friend_list)} 项")
            async with aiofiles.open(self.friend_list_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(friend_list, ensure_ascii=False))
            logger.info("保存friend结束")
        except Exception as e:
            logger.error(f"保存好友列表时发生异常: {e}")
            raise

    async def save_contact_rooms(self, chatroom_list):
        try:
            logger.info(f"准备保存群聊列表，共 {len(chatroom_list)} 项")
            async with aiofiles.open(self.chatroom_list_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(chatroom_list, ensure_ascii=False))
            logger.info("保存rooms结束")
        except Exception as e:
            logger.error(f"保存群聊列表时发生异常: {e}")
            raise


