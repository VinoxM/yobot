import random
import time
import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart


class Scheduler_Custom:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):

        # 这是来自yobot_config.json的设置，如果需要增加设置项，请修改default_config.json文件
        self.setting = glo_setting

        # 这是cqhttp的api，详见cqhttp文档
        self.api = bot_api

        # 注册定时任务，详见apscheduler文档
        @scheduler.scheduled_job('cron',day_of_week='2,6', hour='20',kwargs={"self":self})
        async def abyss(self):
            abyss_imgs = self.setting.get("abyss_img",[])
            abyss_img = abyss_imgs[random.randint(0,len(abyss_imgs)-1)]
            res = "小仓唯提醒您：今晚深渊结算哦~"+"[CQ:image,file=file:///"+self.setting.get("img_path","")+"abyss\\"+abyss_img+"]"
            await self.api.send_group_msg(group_id=902987930, message=res)

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:

        return
