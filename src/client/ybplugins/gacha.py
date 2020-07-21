import asyncio
import json
import math
import os
import pickle
import random
import re
import sqlite3
import time
import aiohttp
from functools import lru_cache
from typing import List, Union, Dict, Tuple
from urllib.parse import urljoin

import requests
from PIL import Image
from quart import Quart

from .templating import render_template
from .yobot_exceptions import CodingError, ServerError


class Gacha:
    Passive = True
    Active = False
    Request = True
    URL = "http://api.yobot.xyz/3.1.4/pool.json"
    Nicknames_csv = "https://github.com/VinoxM/yobot/raw/master/docs/pcr-nickname/nickname3.csv"

    def __init__(self, glo_setting: dict, bot_api, *args, **kwargs):
        self.setting = glo_setting
        self.bot_api = bot_api
        self.pool_file_path = os.path.join(
            self.setting["dirname"], "pool3.json")
        self.resource_path = os.path.join(
            glo_setting['dirname'], 'output', 'resource')
        self.pool_checktime = 0
        self.fix = {
            "jp":"日服",
            "tw":"台服",
            "cn":"国服"
        }
        if not os.path.exists(self.pool_file_path):
            try:
                res = requests.get(self.URL)
            except requests.exceptions.ConnectionError:
                raise ServerError("连接服务器失败")
            if res.status_code != 200:
                raise ServerError(
                    "bad server response. code: "+str(res.status_code))
            with open(self.pool_file_path, "w", encoding="utf-8") as f:
                f.write(res.text)
            self._pool = json.loads(res.text)
        else:
            with open(self.pool_file_path, "r", encoding="utf-8") as f:
                try:
                    self._pool = json.load(f)
                except json.JSONDecodeError:
                    raise CodingError("卡池文件解析错误，请检查卡池文件语法")
        self.nickname_dict: Dict[str, Tuple[str, str]] = {}
        nickfile = os.path.join(glo_setting["dirname"], "nickname3.csv")
        if self.setting.get("nickName_autoUpdate",False) or not os.path.exists(nickfile):
            asyncio.ensure_future(self.update_nicknames(),
                                  loop=asyncio.get_event_loop())
        else:
            with open(nickfile, encoding="utf-8-sig") as f:
                csv = f.read()
                for line in csv.split("\n")[1:]:
                    row = line.split(",")
                    for col in row:
                        self.nickname_dict[col] = (row[0], row[1])
            print("角色昵称加载完成……")

    async def update_nicknames(self):
        print("正在更新角色昵称……")
        nickfile = os.path.join(self.setting["dirname"], "nickname3.csv")
        try:
            async with aiohttp.request('GET', self.Nicknames_csv) as resp:
                if resp.status != 200:
                    raise ServerError(
                        "bad server response. code: " + str(resp.status))
                restxt = await resp.text()
                with open(nickfile, "w", encoding="utf-8-sig") as f:
                    f.write(restxt)
        except aiohttp.ClientError as e:
            raise RuntimeError('错误' + str(e))
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split("\n")[1:]:
                row = line.split(",")
                for col in row:
                    self.nickname_dict[col] = (row[0], row[1])
        print("角色昵称加载完成……")

    def result(self, fix: str) -> dict:
        prop = 0.
        result_list = []
        up_inx = 0
        star1_count = 0
        star2_count = 0
        star3_count = 0
        up_count = 0
        for p in self._pool["pool_"+fix]["pools"].values():
            prop += p["prop"]
        for i in range(self._pool["settings"]["combo"] - 1):
            resu = random.random() * prop
            for p in self._pool["pool_"+fix]["pools"].values():
                resu -= p["prop"]
                if resu < 0:
                    char = random.choice(p["pool"])
                    result_list.append(p.get("prefix", "") + char)
                    if p.get("name", "") == "Pick Up":
                        if up_inx == 0:
                            up_inx = i+1
                        if char in p.get("free_stone", []):
                            up_count += 1
                    if p.get("prefix", "") == "★":
                        star1_count += 1
                    elif p.get("prefix", "") == "★★":
                        star2_count += 1
                    elif p.get("prefix", "") == "★★★":
                        star3_count += 1
                    break
        prop = 0.
        for p in self._pool["pool_"+fix]["pools"].values():
            prop += p["prop_last"]
        resu = random.random() * prop
        for p in self._pool["pool_"+fix]["pools"].values():
            resu -= p["prop_last"]
            if resu < 0:
                result_list.append(p.get("prefix", "") +
                                   random.choice(p["pool"]))
                if p.get("name", "") == "Pick Up" and up_inx == 0:
                    up_inx = self._pool["settings"]["combo"]
                if p.get("prefix", "") == "★★":
                    star2_count += 1
                elif p.get("prefix", "") == "★★★":
                    star3_count += 1
                break
        if self._pool["settings"]["shuffle"]:
            random.shuffle(result_list)
        # print("list:{}\tup:{}".format(result_list,up_inx))
        return {
            "list": result_list,
            "up_inx": up_inx,
            "star1_count": star1_count,
            "star2_count": star2_count,
            "star3_count": star3_count,
            "up_count": up_count
        }

    def gacha(self, qqid: int, nickname: str) -> str:
        # self.check_ver()  # no more updating
        db_exists = os.path.exists(os.path.join(
            self.setting["dirname"], "collections.db"))
        db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "collections.db"))
        db = db_conn.cursor()
        if not db_exists:
            db.execute(
                '''CREATE TABLE Colle(
                qqid INT PRIMARY KEY,
                colle BLOB,
                times SMALLINT,
                last_day CHARACTER(4),
                day_times TINYINT)''')
        today = time.strftime("%m%d")
        sql_info = list(db.execute(
            "SELECT colle,times,last_day,day_times FROM Colle WHERE qqid=?", (qqid,)))
        mem_exists = (len(sql_info) == 1)
        if mem_exists:
            info = pickle.loads(sql_info[0][0])
            times, last_day, day_times = sql_info[0][1:]
        else:
            info = {}
            times, last_day, day_times = 0, "", 0
        day_limit = self._pool["settings"]["day_limit"]
        if today != last_day:
            last_day = today
            day_times = 0
        if day_limit != 0 and day_times >= day_limit:
            return "{}今天已经抽了{}次了，明天再来吧".format(nickname, day_times)
        result = self.result()
        times += 1
        day_times += 1
        reply = ""
        reply += "{}第{}抽：".format(nickname, times)
        for char in result["list"]:
            if char in info:
                info[char] += 1
                reply += "\n{}({})".format(char, info[char])
            else:
                info[char] = 1
                reply += "\n{}(new)".format(char)
        sql_info = pickle.dumps(info)
        if mem_exists:
            db.execute("UPDATE Colle SET colle=?, times=?, last_day=?, day_times=? WHERE qqid=?",
                       (sql_info, times, last_day, day_times, qqid))
        else:
            db.execute("INSERT INTO Colle (qqid,colle,times,last_day,day_times) VALUES(?,?,?,?,?)",
                       (qqid, sql_info, times, last_day, day_times))
        db_conn.commit()
        db_conn.close()
        return reply

    @lru_cache(maxsize=256)
    def check_ssr(self, char, fix: str):
        prop = 0.
        for p in self._pool["pool_"+fix]["pools"].values():
            prop += p["prop"]
        prop = prop*0.05
        for p in self._pool["pool_"+fix]["pools"].values():
            chars = [p.get("prefix", "")+x for x in p["pool"]]
            if char in chars and p["prop"] < prop:
                return True
        return False

    async def thirtytimes(self, qqid: int, nickname: str, fix: str = "jp") -> str:
        # self.check_ver()  # no more updating
        db_exists = os.path.exists(os.path.join(
            self.setting["dirname"], "collections.db"))
        db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "collections.db"))
        db = db_conn.cursor()
        if not db_exists:
            db.execute(
                '''CREATE TABLE Colle(
                qqid INT PRIMARY KEY,
                colle BLOB,
                times SMALLINT,
                last_day CHARACTER(4),
                day_times TINYINT)''')
        today = time.strftime("%m%d")
        sql_info = list(db.execute(
            "SELECT colle,times,last_day,day_times FROM Colle WHERE qqid=?", (qqid,)))
        mem_exists = (len(sql_info) == 1)
        if mem_exists:
            info = pickle.loads(sql_info[0][0])
            times, last_day, day_times = sql_info[0][1:]
        else:
            info = {}
            times, last_day, day_times = 0, "", 0
        day_limit = self._pool["settings"]["day_limit"]
        if today != last_day:
            last_day = today
            day_times = 0
        if day_limit != 0 and day_times+29 > day_limit:
            return "{}今天剩余抽卡次数不足30次，不能抽一井".format(nickname, day_times)
        reply = ""
        result = []
        flag_fully_30_times = True
        ssr_inx = 0
        up_inx = 0
        star1_count = 0
        star2_count = 0
        star3_count = 0
        up_count = 0
        for i in range(1, 31):
            if day_limit != 0 and day_times >= day_limit:
                reply += "{}抽到第{}发十连时已经达到今日抽卡上限，抽卡结果:".format(nickname, i)
                flag_fully_30_times = False
                break
            single_result = self.result(fix)
            if up_inx == 0 and int(single_result["up_inx"]) != 0:
                up_inx = int(single_result["up_inx"])+(i-1)*10
            star1_count += int(single_result["star1_count"])
            star2_count += int(single_result["star2_count"])
            star3_count += int(single_result["star3_count"])
            up_count += int(single_result["up_count"])
            times += 1
            day_times += 1
            for inx, char in enumerate(single_result["list"]):
                if char in info:
                    info[char] += 1
                    if self.check_ssr(char, fix):
                        if ssr_inx == 0:
                            ssr_inx = inx + 1 + (i-1)*10
                        result.append(str(char).replace("★", ""))
                else:
                    info[char] = 1
                    if self.check_ssr(char, fix):
                        if ssr_inx == 0:
                            ssr_inx = inx + 1 + (i-1)*10
                        result.append(str(char).replace("★", ""))
        sql_info = pickle.dumps(info)
        if mem_exists:
            db.execute("UPDATE Colle SET colle=?, times=?, last_day=?, day_times=? WHERE qqid=?",
                       (sql_info, times, last_day, day_times, qqid))
        else:
            db.execute("INSERT INTO Colle (qqid,colle,times,last_day,day_times) VALUES(?,?,?,?,?)",
                       (qqid, sql_info, times, last_day, day_times))
        if len(result) == 0:
            if flag_fully_30_times:
                reply += "[CQ:at, qq={}]-> {}\n太非了，本次下井没有抽到ssr。".format(qqid, self.fix[fix])
            else:
                reply += "[CQ:at, qq={}]-> {}\n本次没有抽到ssr。".format(qqid, self.fix[fix])
            return reply
        if flag_fully_30_times:
            reply += "[CQ:at, qq={}]-> {}\n素敵な仲間が増えますよ！".format(qqid, self.fix[fix], nickname)
        db_conn.commit()
        db_conn.close()
        reply += await self.handle_result(result)
        reply += "\n★★★x{}，★★x{}，★x{}".format(star3_count,star2_count,star1_count)
        reply_free = ""
        if up_count != 0:
            reply_free = "记忆碎片x{}与".format(up_count*100)
        reply += "\n共获得{}女神秘石x{}！".format(reply_free, star1_count+star2_count*10+star3_count*50)
        reply += "\n第{}抽首出虹".format(ssr_inx)
        len_ = -1
        if up_inx != 0:
            reply += "\n第{}抽首出UP角色".format(up_inx)
            len_ = len(result)
        for r in self._pool["replys"].values():
            if len_ in range(r["range"][0], r["range"][1]+1):
                reply += "\n{}".format(random.choice(r["reply"]))
                break
        # print("s1:{},s2:{},s3:{},up:{},upinx:{}".format(star1_count, star2_count, star3_count, up_count,up_inx))
        return reply

    async def handle_result(self,result: List):
        local_files = []
        for r in result:
            char_id = self.nickname_dict[str(r)][0]
            filename = str(char_id)+"31.jpg"
            localfile = os.path.join(self.resource_path, "icon", "unit", filename)
            if not os.path.exists(localfile):
                if filename.endswith('.jpg'):
                    filename = filename[:-4] + '.webp@w400'
                try:
                    while True:
                        async with aiohttp.request(
                                "GET",
                                url=f'https://redive.estertion.win/icon/unit/{filename}'
                        ) as response:
                            res = await response.read()
                            if response.status != 200:
                                filename = '000000.webp@w400'
                                localfile = os.path.join(self.resource_path, "icon", "unit", "000000.jpg")
                            else:
                                break
                except aiohttp.ClientError as e:
                    print(e)
                if not os.path.exists(os.path.dirname(localfile)):
                    os.makedirs(os.path.dirname(localfile))
                with open(localfile, 'wb') as f:
                    f.write(res)
            local_files.append(localfile)
        img_col = 4
        img_row = math.ceil(len(local_files)/img_col)
        img_size = 64
        img_save_path = os.path.join(self.resource_path, "gacha", str(int(time.time()*1000))+".png")
        if not os.path.exists(os.path.dirname(img_save_path)):
            os.makedirs(os.path.dirname(img_save_path))
        to_img = Image.new('RGBA', (img_col*img_size, img_row*img_size))
        for y in range(1, img_row+1):
            for x in range(1, img_col+1):
                from_img = Image.open(local_files[img_row*(y-1)+x-1]).resize((img_size, img_size),Image.ANTIALIAS)
                to_img.paste(from_img, ((x-1)*img_size,(y-1)*img_size))
                if y == img_row and len(local_files) == (img_row-1)*img_col+x:
                    break
        to_img.save(img_save_path)
        return "[CQ:image,file=file:///" + img_save_path + "]"

    async def show_colleV2_async(self, qqid, nickname, cmd: Union[None, str] = None) -> str:
        if not os.path.exists(os.path.join(self.setting["dirname"], "collections.db")):
            return "没有仓库"
        moreqq_list = []
        if cmd != None:
            pattern = r"(?<=\[CQ:at,qq=)\d+(?=\])"
            moreqq_list = [int(x) for x in re.findall(pattern, cmd)]
        db_conn = sqlite3.connect(os.path.join(
            self.setting["dirname"], "collections.db"))
        db = db_conn.cursor()
        sql_info = list(db.execute(
            "SELECT colle FROM Colle WHERE qqid=?", (qqid,)))
        if len(sql_info) != 1:
            db_conn.close()
            return nickname + "的仓库为空"
        colle = pickle.loads(sql_info[0][0])
        more_colle = []
        for other_qq in moreqq_list:
            sql_info = list(db.execute(
                "SELECT colle FROM Colle WHERE qqid=?", (other_qq,)))
            if len(sql_info) != 1:
                db_conn.close()
                return "[CQ:at,qq={}] 的仓库为空".format(other_qq)
            more_colle.append(pickle.loads(sql_info[0][0]))
        db_conn.close()
        if not os.path.exists(os.path.join(self.setting["dirname"], "temp")):
            os.mkdir(os.path.join(self.setting["dirname"], "temp"))
        showed_colle = set(colle)
        for item in more_colle:
            showed_colle = showed_colle.union(item)
        showdata = {"title": "仓库"}
        showdata["header"] = ["角色", nickname]
        for memb in moreqq_list:
            try:
                membinfo = await self.bot_api.get_stranger_info(user_id=memb)
                showdata["header"].append(membinfo["nickname"])
            except:
                showdata["header"].append(str(memb))
        showdata["body"] = []
        for char in sorted(showed_colle):
            line = [char, str(colle.get(char, 0))]
            for item in more_colle:
                line.append(str(item.get(char, 0)))
            showdata["body"].append(line)

        page = await render_template(
            'collection.html',
            data=showdata,
        )

        output_foler = os.path.join(self.setting['dirname'], 'output')
        num = len(os.listdir(output_foler)) + 1
        os.mkdir(os.path.join(output_foler, str(num)))
        filename = 'collection-{}.html'.format(random.randint(0, 999))
        with open(os.path.join(output_foler, str(num), filename), 'w', encoding='utf-8') as f:
            f.write(page)
        reply = urljoin(
            self.setting['public_address'],
            '{}output/{}/{}'.format(
                self.setting['public_basepath'], num, filename))
        if self.setting['web_mode_hint']:
            reply += '\n\n如果无法打开，请仔细阅读教程中《链接无法打开》的说明'
        return reply

    def check_ver(self) -> None:
        auto_update = self._pool["settings"]["auto_update"]
        if not auto_update:
            return
        now = int(time.time())
        if self.pool_checktime < now:
            try:
                res = requests.get(self.URL)
            except requests.exceptions.ConnectionError as c:
                print("无法连接到{}，错误信息：{}".format(self.URL, c))
                return
            if res.status_code == 200:
                online_ver = json.loads(res.text)
                if self._pool["info"]["name"] != online_ver["info"]["name"]:
                    online_ver["settings"] = self._pool["settings"]
                    self._pool = online_ver
                    with open(self.pool_file_path, "w", encoding="utf-8") as pf:
                        pf.write(res.text)
                    print("卡池已自动更新，目前卡池：" + self._pool["info"]["name"])
                self.pool_checktime = now + 80000

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "十连" or cmd == "十连抽":
            return 1
        elif cmd.startswith("仓库"):
            return 4
        elif cmd == "在线十连" or cmd == "在线抽卡":
            return 5
        elif cmd == "抽一井" or cmd == "来一井":
            return 10
        elif cmd == "国服抽一井" or cmd == "国服来一井":
            return 11
        elif cmd == "台服抽一井" or cmd == "台服来一井":
            return 12
        elif cmd == "日服抽一井" or cmd == "日服来一井":
            return 13
        else:
            return 0

    async def execute_async(self, func_num: int, msg: dict):
        if func_num == 5:
            return urljoin(
                self.setting["public_address"],
                '{}gacha/'.format(self.setting['public_basepath'])
            )
        if ((
                msg["message_type"] == "group"
                and not self.setting.get("gacha_on", True))
            or (
                msg["message_type"] == "private"
                and not self.setting.get("gacha_private_on", True))):
            reply = None
        elif func_num == 1:
            reply = self.gacha(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"])
        elif func_num >= 10:
            if func_num == 10:
                fix = self._pool["settings"]["default_pool"]
            elif func_num == 11:
                fix = "cn"
            elif func_num == 12:
                fix = "tw"
            elif func_num == 13:
                fix = "jp"
            reply = await self.thirtytimes(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"],fix=fix)
        elif func_num == 4:
            async def show_colle():
                df_reply = await self.show_colleV2_async(
                    qqid=msg["sender"]["user_id"],
                    nickname=msg["sender"]["card"],
                    cmd=msg["raw_message"][2:],
                )
                replymsg = msg.copy()
                replymsg["message"] = df_reply
                replymsg["at_sender"] = False
                await self.bot_api.send_msg(**replymsg)
            asyncio.ensure_future(show_colle())
            reply = None
        return {
            "reply": reply,
            "block": True
        }

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'gacha/'),
            methods=['GET'])
        async def yobot_gacha():
            return await render_template('gacha.html')
