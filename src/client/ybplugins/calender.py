import datetime
import json
import re

import aiohttp
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from arrow.arrow import Arrow

from .yobot_exceptions import InputError, ServerError

_calender_url = {
    "jp": "https://tools.yobot.win/calender/#jp",
    "tw": "https://pcredivewiki.tw/",
    "cn": "https://tools.yobot.win/calender/#cn",
}


class Event_timeline:
    def __init__(self):
        self._tineline = dict()

    def add_event(self, start_t: Arrow, end_t: Arrow, name):
        t = start_t
        while t <= end_t:
            daystr = t.format(fmt="YYYYMMDD", locale="zh_cn")
            if daystr not in self._tineline:
                self._tineline[daystr] = list()
            self._tineline[daystr].append(name)
            t += datetime.timedelta(days=1)

    def at(self, day: Arrow):
        daystr = day.format(fmt="YYYYMMDD", locale="zh_cn")
        return self._tineline.get(daystr, ())


class Event:
    Passive = True
    Active = True
    Request = False

    def __init__(self, glo_setting: dict, *args, **kwargs):
        self.setting = glo_setting

        # # 时区：东8区
        # self.timezone = datetime.timezone(datetime.timedelta(hours=8))

        # 。。。屁东8区，Arrow这个库解析的时候把时区略了，加东8区会有bug，导致每天早上8点前获取的calendar会延后一天
        self.timezone = datetime.timezone(datetime.timedelta(hours=0))

        self.timeline = None
        self.timeline_jp = None
        self.timeline_tw = None
        self.timeline_cn = None
        self.region={"jp":"日服","tw":"台服","cn":"国服","default":""}

    def load_timeline(self, rg):
        raise RuntimeError("no more sync calling")

    async def load_timeline_async(self, rg=None):
        if rg is None:
            rg = self.setting.get("calender_region", "default")
            timeline_jp = await self.load_timeline_jp_async()
            if timeline_jp is None:
                return
            self.timeline_jp = timeline_jp
            print("刷新日服日程表成功")
            timeline_tw = await self.load_timeline_tw_async()
            if timeline_tw is None:
                return
            self.timeline_tw = timeline_tw
            print("刷新台服日程表成功")
            timeline_cn = await self.load_timeline_cn_async()
            if timeline_cn is None:
                return
            self.timeline_cn = timeline_cn
            print("刷新国服日程表成功")
        if rg == "jp":self.timeline=self.timeline_jp
        elif rg == "tw":self.timeline=self.timeline_tw
        elif rg == "cn":self.timeline=self.timeline_cn
        else:
            self.timeline = None
            if rg != "default":
                print(f"{rg}区域无日程表")

    # def load_time_jp(self, timestamp) -> Arrow:
    #     tz = datetime.timezone(datetime.timedelta(hours=8))
    #     d_time = datetime.datetime.fromtimestamp(timestamp, tz)
    #     a_time = Arrow.fromdatetime(d_time)
    #     if a_time.hour < 4:
    #         a_time -= datetime.timedelta(hours=4)
    #     return a_time

    # async def load_timeline_jp_async(self):
    #     event_source = "https://gamewith.jp/pricone-re/article/show/93857"
    #     try:
    #         async with aiohttp.request("GET", url=event_source) as response:
    #             if response.status != 200:
    #                 raise ServerError(f"服务器状态错误：{response.status}")
    #             res = await response.text()
    #     except aiohttp.client_exceptions.ClientError:
    #         print("日程表加载失败")
    #         return
    #     soup = BeautifulSoup(res, features="html.parser")
    #     events_ids = set()
    #     timeline = Event_timeline()
    #     for event in soup.select("[data-calendar]"):
    #         e = json.loads(event["data-calendar"])
    #         if e["id"] in events_ids:
    #             continue
    #         events_ids.add(e["id"])
    #         timeline.add_event(
    #             self.load_time_jp(e["start_time"]),
    #             self.load_time_jp(e["end_time"]),
    #             e["event_name"],
    #         )
    #     return timeline

    def load_time_jp(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M:%S")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=4):
            a_time -= datetime.timedelta(hours=4)
        return a_time

    async def load_timeline_jp_async(self):
        event_source = "http://toolscdn.yobot.win/calender/jp.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_jp(e["start_time"]),
                self.load_time_jp(e["end_time"]),
                e["name"],
            )
        return timeline

    def load_time_tw(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=5):
            a_time -= datetime.timedelta(hours=5)
        return a_time

    async def load_timeline_tw_async(self):
        event_source = "https://pcredivewiki.tw/static/data/event.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_tw(e["start_time"]),
                self.load_time_tw(e["end_time"]),
                e["campaign_name"],
            )
        return timeline

    def load_time_cn(self, timestr) -> Arrow:
        d_time = datetime.datetime.strptime(timestr, r"%Y/%m/%d %H:%M:%S")
        a_time = Arrow.fromdatetime(d_time)
        if a_time.time() < datetime.time(hour=5):
            a_time -= datetime.timedelta(hours=5)
        return a_time

    async def load_timeline_cn_async(self):
        event_source = "http://toolscdn.yobot.win/calender/cn.json"
        async with aiohttp.request("GET", url=event_source) as response:
            if response.status != 200:
                raise ServerError(f"服务器状态错误：{response.status}")
            res = await response.text()
        events = json.loads(res)
        timeline = Event_timeline()
        for e in events:
            timeline.add_event(
                self.load_time_cn(e["start_time"]),
                self.load_time_cn(e["end_time"]),
                e["name"],
            )
        return timeline

    def get_day_events(self, match_num) -> tuple:
        if match_num == 2 or match_num == 12 or match_num == 22 or match_num == 32:
            daystr = "今天"
            date = Arrow.now(tzinfo=self.timezone)
        elif match_num == 3 or match_num == 13 or match_num == 23 or match_num == 33:
            daystr = "明天"
            date = Arrow.now(tzinfo=self.timezone) + datetime.timedelta(days=1)
        elif match_num & 0xf00000 == 0x100000:
            year = (match_num & 0xff000) >> 12
            month = (match_num & 0xf00) >> 8
            day = match_num & 0xff
            daystr = "{}年{}月{}日".format(2000+year, month, day)
            try:
                date = Arrow(2000+year, month, day)
            except ValueError as v:
                raise InputError("日期错误：{}".format(v))
        if match_num-30>0:
            daystr = "日服"+daystr
            events = self.timeline_jp.at(date)
        elif match_num-20>0:
            daystr = "台服"+daystr
            events = self.timeline_tw.at(date)
        elif match_num-10>0:
            daystr = "国服"+daystr
            events = self.timeline_cn.at(date)
        else:
            daystr = self.region[self.setting.get("calender_region", "default")] + daystr
            events = self.timeline.at(date)
        return (daystr, events)

    def get_week_events(self,match_num) -> str:
        reply = "一周日程："
        preffix = ""
        date = Arrow.now(tzinfo=self.timezone)
        for (k,i) in enumerate(range(7)):
            if match_num-10==4:
                if k==0:preffix += "国服"
                events = self.timeline_cn.at(date)
            elif match_num-20==4:
                if k==0:preffix += "台服"
                events = self.timeline_tw.at(date)
            elif match_num-30==4:
                if k==0:preffix += "日服"
                events = self.timeline_jp.at(date)
            else:
                if k==0:preffix += self.region[self.setting.get("calender_region", "default")]
                events = self.timeline.at(date)
            events_str = "\n⨠".join(events)
            if events_str == "":
                events_str = "没有记录"
            daystr = date.format("MM月DD日")
            reply += "\n======{}======\n⨠{}".format(daystr, events_str)
            date += datetime.timedelta(days=1)
        reply += "\n\n更多日程：{}".format(
            _calender_url.get(self.setting["calender_region"]))
        return preffix+reply

    @staticmethod
    def match(cmd: str) -> int:
        if cmd.find("日程")==-1:
            return 0
        i=0
        if cmd.startswith("国服"):
            i=10
            cmd=cmd[len("国服"):]
        if cmd.startswith("台服"):
            i=20
            cmd=cmd[len("台服"):]
        if cmd.startswith("日服"):
            i=30
            cmd=cmd[len("日服"):]
        if cmd == "日程" or cmd == "日程今日" or cmd == "日程今天":
            return 2+i
        if cmd == "日程明日" or cmd == "日程明天":
            return 3+i
        if cmd == "日程表" or cmd == "日程一周" or cmd == "日程本周":
            return 4+i
        match = re.match(r"日程 ?(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return (0x114000 + 0x100*month + day)
        match = re.match(r"日程 ?(?:20)?(\d{2})年(\d{1,2})月(\d{1,2})[日号]", cmd)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return (0x100000 + 0x1000*year + 0x100*month + day)
        return 1

    def execute(self, match_num: int, msg: dict) -> dict:
        if self.timeline is None:
            if self.setting.get("calender_region", "default") == "default":
                reply = "未设置区服，请发送“{}设置”".format(
                    self.setting.get("preffix_string", ""))
            else:
                reply = "日程表未初始化\n\n更多日程：{}".format(
                    _calender_url.get(self.setting["calender_region"]))
            return {"reply": reply, "block": True}
        if match_num == 1:
            return {"reply": "", "block": True}
        # self.check_and_update()
        if match_num == 4 or match_num == 14 or match_num == 24 or match_num == 34:
            reply = self.get_week_events(match_num)
            return {"reply": reply, "block": True}
        try:
            daystr, events = self.get_day_events(match_num)
        except InputError as e:
            return {"reply": str(e), "block": True}

        events_str = "\n".join(events)
        if events_str == "":
            events_str = "没有记录"
        reply = "{}活动：\n{}".format(daystr, events_str)
        return {"reply": reply, "block": True}

    async def send_daily_async(self):
        print("正在刷新日程表")
        try:
            await self.load_timeline_async()
        except Exception as e:
            print("刷新日程表失败，失败原因："+str(e))
        if not self.setting['calender_on']:
            return
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return
        _, events = self.get_day_events(2)
        events_str = "\n".join(events)
        if events_str is None:
            return
        msg = self.region[self.setting.get("calender_region", "default")]+"今日活动：\n{}".format(events_str)
        sends = []
        for group in sub_groups:
            sends.append({
                "message_type": "group",
                "group_id": group,
                "message": msg
            })
        for userid in sub_users:
            sends.append({
                "message_type": "private",
                "user_id": userid,
                "message": msg
            })
        return sends

    async def send_tomorrow_async(self):
        print("正在刷新日程表")
        try:
            await self.load_timeline_async()
        except Exception as e:
            print("刷新日程表失败，失败原因："+str(e))
        if not self.setting['calender_on']:
            return
        sub_groups = self.setting.get("notify_groups", [])
        sub_users = self.setting.get("notify_privates", [])
        if not (sub_groups or sub_users):
            return
        _, events = self.get_day_events(3)
        events_str = "\n".join(events)
        if events_str is None:
            return
        msg = self.region[self.setting.get("calender_region", "default")]+"明日活动：\n{}".format(events_str)
        sends = []
        for group in sub_groups:
            sends.append({
                "message_type": "group",
                "group_id": group,
                "message": msg
            })
        for userid in sub_users:
            sends.append({
                "message_type": "private",
                "user_id": userid,
                "message": msg
            })
        return sends

    def jobs(self):
        time = self.setting.get("calender_time", "08:00")
        hour, minute = time.split(":")
        trigger = CronTrigger(hour=hour, minute=minute)
        job = (trigger, self.send_daily_async)
        time = self.setting.get("calender_time_tomorrow", "20:30")
        hour1, minute1 = time.split(":")
        trigger1 = CronTrigger(hour=hour1, minute=minute1)
        job1 = (trigger1, self.send_tomorrow_async)
        init_trigger = DateTrigger(
            datetime.datetime.now() +
            datetime.timedelta(seconds=5)
        )  # 启动5秒后初始化
        init_job = (init_trigger, self.load_timeline_async)
        return (job,job1, init_job)
