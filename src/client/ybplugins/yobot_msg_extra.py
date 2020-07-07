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
        # 存储上一条信息
        self.last_msg = None
        # 存储消息重复次数
        self.equal_count = 1
        # 存储上一条复读信息，以免重复复读
        self.last_repeat = None
        self.repeat_count = self.setting.get("repeat_count",2)
        self.repeat_random = self.setting.get("repeat_random",False)
        if self.repeat_random:
            self.repeat_range = self.setting.get("repeat_range",[2,3])
            self.repeat_random_count = random.randint(self.repeat_range[0],self.repeat_range[1])
            print("随机数值为",self.repeat_random_count)
        self.pre_path = "D:\\Documents"

    async def send_img(self,group_id,path):
        res = "[CQ:image,file=file:///"+self.pre_path+"\\Photos"+path+"]"
        await self.api.send_group_msg(group_id=group_id, message=res)
    
    # 发送语音（mirai框架目前未支持）
    async def send_record(self,group_id,path):
        new_path = self.pre_path+"\\Music"+path
        res = "[CQ:record,file=file:///"+new_path+"]"
        await self.api.send_group_msg(group_id=group_id, message=res)

    async def del_file(self,path):
        os.remove(path)

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        # 仅处理群聊消息
        if ctx['message_type'] == 'group':
            # 复读
            # 复读开关
            if self.setting.get("repeat_on",False):
                # 上条信息判断不为空
                if not self.last_msg is None:
                    # 判断是否为过滤信息、是否与上条信息相同、复读信息是否重复
                    if ctx['raw_message']==ctx['message'] and self.last_msg==ctx['message'] and self.last_repeat!=ctx['message']:
                        # 重复信息数加一
                        self.equal_count+=1
                        # 是随机复读值
                        if self.repeat_random:
                            # 达到复读值
                            if self.repeat_random_count==self.equal_count:
                                # 开始复读
                                await self.api.send_group_msg(group_id=ctx['group_id'],message=ctx['message'])
                                # 重置数据
                                self.equal_count=1
                                self.last_repeat=ctx['message']
                                # 重新随机随机数
                                self.repeat_random_count=random.randint(self.repeat_range[0],self.repeat_range[1])
                                print("随机数值为",self.repeat_random_count)
                        # 不是随机复读值
                        else:
                            # 达到复读值    
                            if self.repeat_count==self.equal_count:
                                # 开始复读
                                await self.api.send_group_msg(group_id=ctx['group_id'],message=ctx['message'])
                                # 重置数据
                                self.equal_count=1
                                self.last_repeat=ctx['message']
                    # 当前信息不符合复读要求
                    else:
                        # 记录上一条数据
                        self.last_repeat=ctx['message']
                        # 重置数据
                        self.equal_count=1
                        self.last_repeat=None
                # 上条信息为空
                else:
                    # 存储当前信息为上条信息
                    self.last_msg=ctx['message']


            # curse
            if ctx['raw_message'] != ctx['message']:
                msg = ctx['raw_message']
                if msg.startswith("骂"):
                    res = msg[len("骂"):]
                    filter_ = ["傻逼","煞笔","沙比","sb"]
                    for i in filter_:
                        if res.find(i)!=-1:
                            if res.find("我")!=-1:res=res.replace("我","你")
                            if res.find("xcw")!=-1:res=res.replace("xcw","你")
                            await self.api.send_group_msg(group_id=ctx["group_id"], message=res)
                            return
                    await self.api.send_group_msg(group_id=ctx["group_id"], message="不骂，爬")