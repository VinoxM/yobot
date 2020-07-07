import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

# 信息额外处理插件
class Message_Extra:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        # 加载配置文件
        self.setting = glo_setting
        # 加载bot的api
        self.api = bot_api
        # 存储上一条信息和上上条信息
        self.last_msg = self.pre_last_msg = None
        # 存储上一条复读信息，以免重复复读
        self.last_repeat = None

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        # 仅处理群聊消息
        if ctx['message_type'] == 'group':
            # 复读
            # 判断上条和上上条信息是否已有值
            if ctx['raw_message'] == ctx['message']:
                if not self.last_msg is None and not self.pre_last_msg is None:
                    # 判断上条信息和上上条信息相同
                    if self.last_msg == self.pre_last_msg:
                        msg = ctx['message']
                        # 判断发送的信息和前两条信息相同
                        if self.last_msg == msg and not self.last_repeat == msg:
                            # 开始复读，发送复读信息
                            await self.api.send_group_msg(group_id=ctx["group_id"], message=msg)
                            # 记录本次复读信息
                            self.last_repeat = msg
                self.last_msg = ctx['message']
                self.pre_last_msg = self.last_msg

            # curse
            if ctx['raw_message'] != ctx['message']:
                msg = ctx['raw_message']
                if msg.startswith("骂"):
                    res = msg[len("骂"):]
                    filter_ = ["傻逼","煞笔","沙比","sb"]
                    for i in filter_:
                        if res.find(i)!=-1:
                            await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                            return
                    await self.api.send_group_msg(group_id=ctx["group_id"], message="不骂，爬")
                    