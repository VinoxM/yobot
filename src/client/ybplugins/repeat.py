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
        self.setting = glo_setting
        self.api = bot_api
        self.last_msg = self.pre_last_msg = None
        self.last_repeat = None

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        if not self.last_msg is None and not self.pre_last_msg is None:
            if self.last_msg == self.pre_last_msg:
                msg = ctx['raw_message']
                if self.last_msg == msg and not self.last_repeat == msg:
                    await self.api.send_private_msg(user_id=ctx["user_id"], message=msg)
                    self.last_msg = self.pre_last_msg = None
                    self.last_repeat = msg
        self.last_msg = ctx['raw_message']
        self.pre_last_msg = self.last_msg
