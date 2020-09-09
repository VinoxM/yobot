import os
import random
import time
import asyncio
from typing import Any, Dict, Union

from aiocqhttp import ActionFailed
from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
        async def job_func(group_ids: list, msg: str, index: int):
            for i in group_ids:
                tri = self.setting.get("trigger", [])[index]
                msg_img = ""
                if tri.get("img_on", False):
                    img_path = os.path.join(self.setting.get("base_file_path", ""), self.setting.get("img_path", ""), tri.get("img_path", ""))
                    imgs = os.listdir(img_path)
                    img_name = imgs[random.randint(0, len(imgs) - 1)]
                    img = os.path.join(img_path, img_name)
                    msg_img = "[CQ:image,file=file:///" + img + "]"
                if msg.find("{}") > -1:
                    msg = msg.join(msg_img)
                else:
                    msg = msg + msg_img
                try:
                    await self.api.send_group_msg(group_id=i, message=msg)
                except ActionFailed as e:
                    print("Scheduler Plugins send message failed.Cause by retcode:{}".join(e.retcode))

        trigger = self.setting.get("trigger", [])
        self.triggers = {}
        for k, i in enumerate(trigger):
            corn = CronTrigger(
                year=i.get("year", None) if i.get("year", None) != '*' else None,
                month=i.get("month", None) if i.get("month", None) != '*' else None,
                day=i.get("day", None) if i.get("day", None) != '*' else None,
                week=i.get("week", None) if i.get("week", None) != '*' else None,
                day_of_week=i.get("day_of_week", None) if i.get("day_of_week", None) != '*' else None,
                hour=i.get("hour", None) if i.get("hour", None) != '*' else None,
                minute=i.get("minute", None) if i.get("minute", None) != '*' else None,
                second=i.get("second", None) if i.get("second", None) != '*' else None,
                start_date=i.get("start_date", None) if i.get("start_date", None) != '*' else None,
                end_date=i.get("end_date", None) if i.get("end_date", None) != '*' else None,
                timezone=i.get("timezone", None) if i.get("timezone", None) != '*' else None,
                jitter=i.get("jitter", None) if i.get("jitter", None) != 0 else None)
            msgs = i.get("msg", [])
            msg = msgs[random.randint(0, len(msgs)-1)]
            group_ids = i.get("groups", [])
            sch = AsyncIOScheduler()
            sch.add_job(job_func, corn, kwargs={"group_ids": group_ids, "msg": msg, "index": k})
            sch.start()
            label_ = i.get("label", "") + "\n"
            for j in group_ids:
                if self.triggers.__contains__(j):
                    self.triggers[j].append(label_)
                else:
                    self.triggers[j] = [label_]

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        if ctx['raw_message'] == "查看定时器":
            labels = self.triggers[ctx["group_id"]]
            msg = "该群共有" + str(len(labels)) + "个定时器\n"
            for i in labels:
                msg += i
            await self.api.send_group_msg(group_id=ctx["group_id"], message=msg)
        return
