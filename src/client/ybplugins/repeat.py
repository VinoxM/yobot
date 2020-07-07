import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

# 复读插件
class Repeat:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        #加载配置文件
        self.setting = glo_setting
        #加载bot的api
        self.api = bot_api
        #存储上一条信息和上上条信息
        self.last_msg = self.pre_last_msg = None
        #存储上一条复读信息，以免重复复读
        self.last_repeat = None

    def _withPreffix(self,msg):
        if self.setting.get("preffix_on",False):
            pres = self.setting.get("preffix_string",None)
            if not pres is None:
                for i in pres:
                    if msg.startswith(i):return True
        return False

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        #判断上条和上上条信息是否已有值
        if ctx['message_type'] == 'group':
            if not self.last_msg is None and not self.pre_last_msg is None:
                #判断上条信息和上上条信息相同
                if self.last_msg == self.pre_last_msg:
                    msg = ctx['raw_message']
                    #判断发送的信息和前两条信息相同
                    if self.last_msg == msg and not self.last_repeat == msg:
                        #开始复读，发送复读信息
                        await self.api.send_group_msg(group_id=ctx["group_id"], message=msg)
                        #记录本次复读信息
                        self.last_repeat = msg
            self.last_msg = ctx['raw_message']
            self.pre_last_msg = self.last_msg
