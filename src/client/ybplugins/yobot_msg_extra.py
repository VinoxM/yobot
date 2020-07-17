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
                    if i.get("prefix",False):self.extras_pre.append(i)
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
                keyword = i.get("keyword","")
                if i.get("full_keyword",False):
                    flag = (msg == keyword)
                else:
                    flag = msg.startswith(keyword)
                if flag:
                    res = msg[len(keyword):]
                    if i.get("filter_on", False):
                        filter_ = i.get("filter_", [])
                        res_f = True
                        for j in filter_:
                            if res.find(j)!=-1:
                                res_f = False
                                if i.get("replace_on", False):
                                    for k in i.get("replace_", []):
                                        res = res.replace(k[0], k[1])
                                break
                        if res_f:
                            len_ = len(i.get("result_", []))
                            ran = random.randint(0, len_ - 1)
                            res = i.get("result_", [])[ran]
                        await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                        return
                    else:
                        if i.get("replace_on", False):
                            for k in i.get("replace_", []):
                                res = res.replace(k[0], k[1])
                    if i.get("result_on", False):
                        len1_ = len(i.get("result_",[]))
                        ran = random.randint(0, len1_-1)
                        res_ = i.get("result_", [])[ran]
                        if res_ == 'result':
                            res = ctx['raw_message'][len(keyword):]
                        elif res_ == 'record':
                            re_path = self.setting.get("record_path", "")
                            re_folder = i.get("record_folder", False)
                            if re_folder:
                                re_list = os.listdir(re_path + re_folder)
                                re_len_ = len(re_list)
                                re_ran = random.randint(0, re_len_-1)
                                r_name = re_folder + re_list[re_ran]
                            else:
                                r_len_ = len(i.get("record_folder", []))
                                r_ran = random.randint(0, r_len_-1)
                                r_name = i.get("record_folder", [])[r_ran]
                            new_path = re_path + r_name
                            res = "[CQ:record,file=file:///" + new_path + "]"
                        else:
                            res = res_
                    await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                    return
