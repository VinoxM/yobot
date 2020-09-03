'''
自定义功能：

在这里可以编写自定义的功能，
编写完毕后记得 git commit，

这个模块只是为了快速编写小功能，如果想编写完整插件可以使用：
https://github.com/richardchien/python-aiocqhttp
或者
https://github.com/richardchien/nonebot

关于PR：
如果基于此文件的PR，请在此目录下新建一个`.py`文件，并修改类名
然后在`yobot.py`中添加`import`（这一步可以交给仓库管理者做）
'''

import asyncio
from typing import Any, Dict, Union

import aiohttp
import feedparser
from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart


class Custom:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        '''
        初始化，只在启动时执行一次

        参数：
            glo_setting 包含所有设置项，具体见default_config.json
            bot_api 是调用机器人API的接口，具体见<https://python-aiocqhttp.cqp.moe/>
            scheduler 是与机器人一同启动的AsyncIOScheduler实例
            app 是机器人后台Quart服务器实例
        '''
        # 注意：这个类加载时，asyncio事件循环尚未启动，且bot_api没有连接
        # 此时不要调用bot_api
        # 此时没有running_loop，不要直接使用await，请使用asyncio.ensure_future并指定loop=asyncio.get_event_loop()

        # 如果需要启用，请注释掉下面一行
        return

        # 这是来自yobot_config.json的设置，如果需要增加设置项，请修改default_config.json文件
        self.setting = glo_setting

        # 这是cqhttp的api，详见cqhttp文档
        self.api = bot_api

        # # 注册定时任务，详见apscheduler文档
        # @scheduler.scheduled_job('cron', hour=8)
        # async def good_morning():
        #     await self.api.send_group_msg(group_id=123456, message='早上好')

        # # 注册web路由，详见flask与quart文档
        # @app.route('/is-bot-running', methods=['GET'])
        # async def check_bot():
        #     return 'yes, bot is running'

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        '''
        每次bot接收有效消息时触发

        参数ctx 具体格式见：https://cqhttp.cc/docs/#/Post
        '''
        # 注意：这是一个异步函数，禁止使用阻塞操作（比如requests）

        # 如果需要使用，请注释掉下面一行
        return

        cmd = ctx['raw_message']
        if cmd == 'test' and ctx["message_type"] == 'private':
            # 调用api发送消息，详见cqhttp文档
            try:
                async with aiohttp.request('GET', url="https://raw.githubusercontent.com/VinoxM/yobot/master/docs/v3/ver.json", headers={"content-type": "application/json", "User-Agent": ""},
                                           timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(response)
            except Exception as e:
                print(e)
            # await self.api.send_private_msg(
            #     user_id=ctx["user_id"], message='收到问好[CQ:image,proxy=1,url=https://pbs.twimg.com/media/Eg9XFzZUcAEWnFw?format=jpg&name=orig]')

            # 返回字符串：发送消息并阻止后续插件
            # return ''

            # async with aiohttp.ClientSession() as session:
            #     async with session.get("http://rsshub.app.cdn.cloudflare.net/twitter/user/priconne_redive",
            #                            headers={"host": "rsshub.app"}) as response:
            #         res = await response.text()
            #         feed = feedparser.parse(res)
            #         for item in feed["entries"]:
            #             m = {"title": item["title"], "link": item["link"]}
            #             summary = item["summary"]
            #             i_start = summary.find("<img")
            #             if i_start > -1:
            #                 i_end = summary.find(">", i_start)
            #                 img = summary[i_start:i_end]
            #                 summary.replace(img, "")
            #                 src_s = img.find("src=")
            #                 src_e = img.find("\"", src_s + 5)
            #                 src = img[src_s + 5:src_e]
            #                 m["title"] += "\n[CQ:img,url={}]".format(src)
            #                 await self.api.send_private_msg(user_id=ctx["user_id"],message=m["title"])
            #                 break
        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
