import asyncio
import os
import random
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
        extras = self.setting.get("extra",[])
        self.extras_pre = []
        self.extras_ = []
        
        if len(extras)>0:
            for i in extras:
                if i.get("on",False):
                    if i.get("preffix",False):self.extras_pre.append(i)
                    else:self.extras_.append(i)
                

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        # 仅处理群聊消息
        if ctx['message_type'] == 'group':
            msg = ctx['raw_message']
            if ctx['raw_message'] != ctx['message']:
                extras = self.extras_pre
            else:
                extras = self.extras_
            for i in extras:
                if i.get("keyword_on",False):
                    keyword = i.get("keyword",False)
                    if not keyword:flag=(msg==i.get("full_keyword",""))
                    else:flag=msg.startswith(keyword)
                    if flag:
                        res = msg[len(keyword):]
                        if i.get("filter_on",False):
                            filter_ = i.get("filter",[])
                            res_f = True
                            for j in filter_:
                                if res.find(j)!=-1:
                                    res_f = False
                                    if i.get("replace_on",False):
                                        for k in i.get("replace",[]):
                                            res = res.replace(k[0],k[1])
                                    break
                            if res_f:
                                len_ = len(i.get("result", []))
                                ran = random.randint(0, len_ - 1)
                                res = i.get("result", [])[ran]
                                await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                                return
                        else:
                            if i.get("replace_on", False):
                                for k in i.get("replace", []):
                                    res = res.replace(k[0], k[1])
                        if not i.get("result_on",False):
                            len_ = len(i.get("result",[]))
                            ran = random.randint(0,len_-1)
                            if i.get("result",[])[ran]=='result':res = ctx['raw_message'][len(keyword):]
                            else:res = i.get("result",[])[ran]
                        await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                        return