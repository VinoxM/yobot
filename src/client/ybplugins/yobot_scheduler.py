import random
import time
import asyncio
from typing import Any, Dict, Union

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
        async def job_func(group_ids:list,msg,index):
            for i in group_ids:
                tri = self.setting.get("trigger",[])[index]
                title = tri.get("title",None)
                if tri.get("img_on",False):
                    imgs = tri.get("imgs",[])
                    img = imgs[random.randint(0,len(imgs)-1)]
                    img_path = ""
                    if title is None:img_path=self.setting.get("img_path","")+img
                    else:img_path=self.setting.get("img_path","")+title+"\\"+img
                    msg += "[CQ:image,file=file:///"+img_path+"]"
                await self.api.send_group_msg(group_id=i, message=msg)

        trigger = self.setting.get("trigger",[])
        self.triggers = {}
        for k,i in enumerate(trigger):
            corn = CronTrigger(year= i.get("year",None),month= i.get("month",None),day= i.get("day",None),week= i.get("week",None),day_of_week= i.get("day_of_week",None),hour= i.get("hour",None),minute= i.get("minute",None),second= i.get("second",None),start_date= i.get("start_date",None),end_date= i.get("end_date",None),timezone= i.get("timezone",None),jitter= i.get("jitter",None))
            msg = i.get("msg","")
            group_ids=i.get("groups",[])
            sch = AsyncIOScheduler()
            sch.add_job(job_func,corn,kwargs={"group_ids":group_ids,"msg":msg,"index":k})
            sch.start()                
            label_ = i.get("label","")+"\n"
            for j in group_ids:
                if self.triggers.__contains__(j):self.triggers[j].append(label_)
                else:self.triggers[j]=[label_]

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        if ctx['raw_message']=="查看定时器":
            labels = self.triggers[ctx["group_id"]]
            msg = "该群共有"+str(len(labels))+"个定时器\n"
            for i in labels:
                msg+=i
            await self.api.send_group_msg(group_id=ctx["group_id"], message=msg)
        return
