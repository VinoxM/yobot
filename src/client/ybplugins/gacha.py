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
    URL = "https://raw.githubusercontent.com/VinoxM/yobot/master/docs/pcr-pools/pool.json"
    Nicknames_csv = "https://raw.githubusercontent.com/VinoxM/yobot/master/docs/pcr-nickname/nickname3.csv"

    def __init__(self, glo_setting: dict, bot_api, *args, **kwargs):
        self.setting = glo_setting
        self.bot_api = bot_api
        self.pool_file_path = os.path.join(
            self.setting["dirname"], "pool3.json")
        self.resource_path = os.path.join(
            glo_setting['dirname'], 'output', 'resource')
        self.pool_checktime = 0
        self.pool_up = {}
        self.fix = {
            "jp": "日服",
            "tw": "台服",
            "cn": "国服"
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
        self.init_pool_pickUp()
        self.nickname_dict: Dict[str, Tuple[str, str]] = {}
        self.init_nickName()
        # nickfile = os.path.join(glo_setting["dirname"], "nickname3.csv")
        # if self.setting.get("nickName_autoUpdate",False) or not os.path.exists(nickfile):
        #     asyncio.ensure_future(self.update_nicknames(),
        #                           loop=asyncio.get_event_loop())
        # else:
        #     with open(nickfile, encoding="utf-8-sig") as f:
        #         csv = f.read()
        #         for line in csv.split("\n")[1:]:
        #             row = line.split(",")
        #             for col in row:
        #                 self.nickname_dict[col] = (row[0], row[1])
        #     print("角色昵称加载完成……")

    def init_nickName(self)->str:
        character=self._pool["character"]
        for type in character:
            for star in character[type]:
                for char in character[type][star]:
                    self.nickname_dict[character[type][star][char][1]]=(char, character[type][star][char][0])
        print("昵称加载完成……")
        return "昵称加载完成……";

    async def reload_nickName(self):
        return self.init_nickName();

    def init_pool_pickUp(self):
        self.pool_up = {
            "jp": {
                "★": [],
                "★★": [],
                "★★★": [],
                "all": 0,
                "up": [],
                "title": ""
            },
            "tw": {
                "★": [],
                "★★": [],
                "★★★": [],
                "all": 0,
                "up": [],
                "title": ""
            },
            "cn": {
                "★": [],
                "★★": [],
                "★★★": [],
                "all": 0,
                "up": [],
                "title": ""
            }
        }
        for k in self.pool_up.keys():
            for v in self._pool["pool_"+k]["pools"].values():
                if v["name"] == "Pick Up":
                    self.pool_up[k][v["prefix"]] += v["pool"]
                    self.pool_up[k]["all"] += len(v["pool"])
                    for char in v["pool"]:
                        self.pool_up[k]["up"].append(v["prefix"]+char)
            if self.pool_up[k]["all"] > 0:
                self.pool_up[k]["title"] = ">Pick Up："
                if len(self.pool_up[k]["★★★"]) > 0:
                    self.pool_up[k]["title"] += "★★★：{}，".format(",".join(self.pool_up[k]["★★★"]))
                if len(self.pool_up[k]["★★"]) > 0:
                    self.pool_up[k]["title"] += "★★：{}，".format(",".join(self.pool_up[k]["★★"]))
                if len(self.pool_up[k]["★"]) > 0:
                    self.pool_up[k]["title"] += "★：{}，".format(",".join(self.pool_up[k]["★"]))
                self.pool_up[k]["title"] = self.pool_up[k]["title"][:-1]
            else:
                self.pool_up[k]["title"] = ">白金蛋池"


    async def update_nicknames(self, flag: bool = False) -> str:
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
            raise RuntimeError('错误:' + str(e))
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split("\n")[1:]:
                row = line.split(",")
                for col in row:
                    self.nickname_dict[col] = (row[0], row[1])
        reply = "角色昵称加载完成……"
        print(reply)
        if flag:
            return reply

    def result(self, fix: str, up_count: dict = {}) -> dict:
        prop = 0.
        result_list = []
        up_inx = 0
        star1_count = 0
        star2_count = 0
        star3_count = 0
        free_count = 0
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
                        if up_count.get(p["prefix"]+char, -1) > -1:
                            up_count[p["prefix"]+char] += 1
                        if up_inx == 0:
                            up_inx = i+1
                        if char in p.get("free_stone", []):
                            free_count += 1
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
                char = random.choice(p["pool"])
                result_list.append(p.get("prefix", "") + char)
                if p.get("name", "") == "Pick Up":
                    if up_count.get(p["prefix"]+char, -1) > -1:
                        up_count[p["prefix"]+char] += 1
                    if up_inx == 0:
                        up_inx = 10
                    if char in p.get("free_stone", []):
                        free_count += 1
                elif p.get("prefix", "") == "★★":
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
            "up_count": up_count,
            "free_count": free_count
        }

    async def gacha(self, qqid: int, nickname: str , fix: str) -> str:
        # await self.check_ver()  # no more updating
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
        result_single = self.result(fix)
        result = []
        times += 1
        day_times += 1
        reply = ""
        reply += "[CQ:at, qq={}]-> {}\n第{}抽：".format(qqid, self.fix[fix], times)
        # reply += "{}-> {}\n第{}抽：".format(nickname, self.fix[fix], times)
        for char in result_single["list"]:
            if char in info:
                info[char] += 1
            else:
                info[char] = 1
            result.append([str(char).replace("★", ""), str(char).count("★")])
        sql_info = pickle.dumps(info)
        if mem_exists:
            db.execute("UPDATE Colle SET colle=?, times=?, last_day=?, day_times=? WHERE qqid=?",
                       (sql_info, times, last_day, day_times, qqid))
        else:
            db.execute("INSERT INTO Colle (qqid,colle,times,last_day,day_times) VALUES(?,?,?,?,?)",
                       (qqid, sql_info, times, last_day, day_times))
        reply += await self.handle_result(result)
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
            if p.get("prefix","") == "★★★":
                chars = [p.get("prefix", "")+x for x in p["pool"]]
                if char in chars and p["prop"] < prop:
                    return True
        return False

    async def thirtytimes(self, qqid: int, nickname: str, fix: str) -> str:
        # await self.check_ver()  # no more updating
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
        free_count = 0
        up_count = {"all": 0}
        for char in self.pool_up[fix]["up"]:
            up_count[char] = 0
        for i in range(1, 31):
            if day_limit != 0 and day_times >= day_limit:
                reply += "{}抽到第{}发十连时已经达到今日抽卡上限，抽卡结果:".format(nickname, i)
                flag_fully_30_times = False
                break
            single_result = self.result(fix,up_count)
            if up_inx == 0 and int(single_result["up_inx"]) != 0:
                up_inx = int(single_result["up_inx"])+(i-1)*10
            star1_count += int(single_result["star1_count"])
            star2_count += int(single_result["star2_count"])
            star3_count += int(single_result["star3_count"])
            free_count += int(single_result["free_count"])
            all_ = 0
            for c in up_count.keys():
                if c == "all":
                    continue
                # up_count[c] += int(single_result["up_count"][c])
                all_ += up_count[c]
            up_count["all"] = all_
            times += 1
            day_times += 1
            for inx, char in enumerate(single_result["list"]):
                if char in info:
                    info[char] += 1
                    if self.check_ssr(char, fix):
                        if ssr_inx == 0:
                            ssr_inx = inx + 1 + (i-1)*10
                        result.append([str(char).replace("★", ""), str(char).count("★"), str(char) in self.pool_up[fix]["up"]])
                else:
                    info[char] = 1
                    if self.check_ssr(char, fix):
                        if ssr_inx == 0:
                            ssr_inx = inx + 1 + (i-1)*10
                        result.append([str(char).replace("★", ""), str(char).count("★"), str(char) in self.pool_up[fix]["up"]])
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
            reply += "[CQ:at, qq={}] > {}\n{}\n素敵な仲間が増えますよ！".format(qqid, self.fix[fix], self.pool_up[fix]["title"])
            # reply += "{} > {}\n{}\n素敵な仲間が増えますよ！".format(nickname, self.fix[fix], self.pool_up[fix]["title"])
        db_conn.commit()
        db_conn.close()
        reply += await self.handle_result(result)
        reply += "\n共计：★★★x{}，★★x{}，★x{}".format(star3_count, star2_count, star1_count)
        if up_count["all"] > 0:
            reply += "\nPick Up："
            for c in up_count.keys():
                if c == "all":
                    continue
                reply += "{}x{}，".format(c, up_count[c])
            reply = reply[:-1]
        reply_free = ""
        if free_count != 0:
            reply_free = "记忆碎片x{}与".format(free_count*100)
        reply += "\n共获得{}女神秘石x{}！".format(reply_free, star1_count+star2_count*10+star3_count*50)
        reply += "\n第{}抽首出虹，".format(ssr_inx)
        len_ = star3_count
        if up_inx != 0:
            reply += "第{}抽首出UP角色".format(up_inx)
        else:
            reply += "没有抽到UP角色"
            len_ = -1
        if len_ < 5 and free_count >= 2:
            len_ = -2
        for r in self._pool["replys"].values():
            if len_ in range(r["range"][0], r["range"][1]+1):
                reply += "\n{}".format(random.choice(r["reply"]))
                break
        # print("s1:{},s2:{},s3:{},up:{},upinx:{}".format(star1_count, star2_count, star3_count, up_count,up_inx))
        return reply

    async def handle_result(self,result: List):
        # print(result)
        local_files = []
        for r in result:
            char_id = self.nickname_dict[str(r[0])][0]
            filename = str(char_id)
            if r[1] < 3:
                filename += "11.jpg"
            else:
                filename += "31.jpg"
            localfile = os.path.join(self.resource_path, "icon", "unit", str(r[1]), filename)
            if not os.path.exists(localfile):
                if filename.endswith('.jpg'):
                    filename_ = filename[:-4] + '.webp@w400'
                try:
                    while True:
                        async with aiohttp.request(
                                "GET",
                                url=f'https://redive.estertion.win/icon/unit/{filename_}'
                        ) as response:
                            res = await response.read()
                            if response.status != 200:
                                filename_ = '000000.webp@w400'
                                localfile = os.path.join(self.resource_path, "icon", "unit", "000000.jpg")
                            else:
                                break
                except aiohttp.ClientError as e:
                    print(e)
                if not os.path.exists(os.path.dirname(localfile)):
                    os.makedirs(os.path.dirname(localfile))
                with open(localfile, 'wb') as f:
                    f.write(res)
            if r[2]:
                gacha_path = os.path.join(self.resource_path, "gacha", "unit","pickup", str(r[1]))
            else:
                gacha_path = os.path.join(self.resource_path, "gacha", "unit", str(r[1]))
            if not os.path.exists(gacha_path):
                os.makedirs(gacha_path)
            gacha_file = os.path.join(gacha_path, filename[:-4]+".png")
            if not os.path.exists(gacha_file):
                star_size = 36
                gacha_star = Image.open(os.path.join(self.resource_path, "gacha", "unit", "star.png")).resize((star_size, star_size), Image.ANTIALIAS).convert('RGBA')
                gacha_img = Image.open(localfile).resize((128, 128), Image.ANTIALIAS).convert('RGBA')
                for i in range(1, r[1]+1):
                    gacha_img.paste(gacha_star, (int(star_size*(i*0.6-0.7)), 128-star_size), mask=gacha_star.split()[3])
                if r[2]:
                    gacha_pick_up = Image.open(os.path.join(self.resource_path, "gacha", "unit", "up.png")).resize((60, 24), Image.ANTIALIAS).convert('RGBA')
                    gacha_img.paste(gacha_pick_up, (76, 0), mask=gacha_pick_up.split()[3])
                gacha_img.save(gacha_file)
            local_files.append(gacha_file)
        img_col = 5
        img_row = math.ceil(len(local_files)/img_col)
        img_size = 96
        img_split_x = 5
        img_split_y = 5
        img_save_path = os.path.join(self.resource_path, "gacha", str(int(time.time()*1000))+".png")
        if not os.path.exists(os.path.dirname(img_save_path)):
            os.makedirs(os.path.dirname(img_save_path))
        to_img = Image.new('RGBA', (img_col*img_size+img_split_x*(img_col-1), img_row*img_size+img_split_y*(img_row-1)))
        for y in range(1, img_row+1):
            for x in range(1, img_col+1):
                from_img = Image.open(local_files[img_col*(y-1)+x-1]).resize((img_size, img_size),Image.ANTIALIAS)
                to_img.paste(from_img, ((x-1)*(img_size+img_split_x), (y-1)*(img_size+img_split_y)))
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

    async def check_ver(self, flag: bool = False, pool: bool = False) -> str:
        print("正在更新卡池……")
        auto_update = self._pool["settings"]["auto_update"]
        if not flag and not auto_update:
            return
        now = int(time.time())
        if flag or self.pool_checktime < now:
            reply = ""
            try:
                res = requests.get(self.URL)
            except requests.exceptions.ConnectionError as c:
                # raise RuntimeError('错误:' + str(c))
                reply = "更新失败：无法连接到服务器！"
                print(reply)
                self.pool_checktime = now + 3600
                return reply
            if res.status_code == 200:
                online_ver = json.loads(res.text)
                if self._pool["info"].get("ver", 20991231) == 20991231 or self._pool["info"]["ver"] < online_ver["info"]["ver"]:
                    # online_ver["settings"] = self._pool["settings"]
                    self._pool["character"] = online_ver["character"]
                    if pool:
                        self._pool["pool_jp"] = online_ver["pool_jp"]
                        self._pool["pool_tw"] = online_ver["pool_tw"]
                        self._pool["pool_cn"] = online_ver["pool_cn"]
                    self._pool["info"]["ver"] = online_ver["info"]["ver"]
                    with open(self.pool_file_path, "w", encoding="utf-8") as pf:
                        pf.write(json.dumps(self._pool,ensure_ascii=False,indent=2))
                    with open(self.pool_file_path, "r", encoding="utf-8") as f:
                        try:
                            self._pool = json.load(f)
                        except json.JSONDecodeError:
                            raise CodingError("卡池文件解析错误，请检查卡池文件语法")
                    self.init_nickName()
                    if pool:
                        self.init_pool_pickUp()
                    reply = "卡池已自动更新：{}".format(str(self._pool["info"]["ver"]))
                else:
                    reply = "卡池已经是最新：{}".format(str(self._pool["info"]["ver"]))
                print(reply)
                self.pool_checktime = now + 3600
                return reply

    async def reload_pool(self) -> str:
        print("正在加载卡池……")
        with open(self.pool_file_path, "r", encoding="utf-8") as f:
            try:
                self._pool = json.load(f)
            except json.JSONDecodeError:
                raise CodingError("卡池文件解析错误，请检查卡池文件语法")
        self.init_pool_pickUp()
        print("加载卡池成功……")
        return "加载卡池成功，当前版本：{}".format(str(self._pool["info"]["ver"]))

    @staticmethod
    def match(cmd: str) -> int:
        if cmd == "十连" or cmd == "十连抽":
            return 1
        if cmd == "国服十连" or cmd == "国服十连抽":
            return 2
        if cmd == "台服十连" or cmd == "台服十连抽":
            return 3
        if cmd == "日服十连" or cmd == "日服十连抽":
            return 4
        elif cmd.startswith("仓库"):
            return 5
        elif cmd == "在线十连" or cmd == "在线抽卡":
            return 6
        elif cmd == "抽一井" or cmd == "来一井":
            return 20
        elif cmd == "国服抽一井" or cmd == "国服来一井":
            return 21
        elif cmd == "台服抽一井" or cmd == "台服来一井":
            return 22
        elif cmd == "日服抽一井" or cmd == "日服来一井":
            return 23
        elif cmd == "更新卡池角色":
            return 7
        elif cmd == "更新卡池":
            return 17
        elif cmd == "重载卡池":
            return 18
        elif cmd == "卡池版本":
            return 8
        elif cmd == "更新昵称":
            return 9
        elif cmd == "重载昵称":
            return 19
        else:
            return 0

    async def execute_async(self, func_num: int, msg: dict):
        if func_num == 6:
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
        elif func_num <= 4:
            if func_num == 1:
                fix = self._pool["settings"]["default_pool"]
            elif func_num == 2:
                fix = "cn"
            elif func_num == 3:
                fix = "tw"
            elif func_num == 4:
                fix = "jp"
            reply = await self.gacha(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"],fix=fix)
        elif func_num == 5:
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
        elif func_num == 7:
            if msg["message_type"] == "group":
                await self.bot_api.send_group_msg(group_id=msg["group_id"], message="正在更新卡池角色……")
            if msg["message_type"] == "private":
                await self.bot_api.send_private_msg(user_id=msg["sender"]["user_id"], message="正在更新卡池角色……")
            reply = await self.check_ver(flag=True, pool=False)
        elif func_num == 17:
            if msg["message_type"] == "group":
                await self.bot_api.send_group_msg(group_id=msg["group_id"], message="正在更新卡池……")
            if msg["message_type"] == "private":
                await self.bot_api.send_private_msg(user_id=msg["sender"]["user_id"], message="正在更新卡池……")
            reply = await self.check_ver(flag=True, pool=True)
        elif func_num == 8:
            reply = "当前卡池版本:{}".format(self._pool["info"]["ver"])
        elif func_num == 18:
            if msg["message_type"] == "group":
                await self.bot_api.send_group_msg(group_id=msg["group_id"], message="正在重载卡池……")
            if msg["message_type"] == "private":
                await self.bot_api.send_private_msg(user_id=msg["sender"]["user_id"], message="正在重载卡池……")
            reply = await self.reload_pool();
        elif func_num == 9:
            if msg["message_type"] == "group":
                await self.bot_api.send_group_msg(group_id=msg["group_id"], message="正在更新昵称……")
            elif msg["message_type"] == "private":
                await self.bot_api.send_private_msg(user_id=msg["sender"]["user_id"], message="正在更新昵称……")
            reply = await self.update_nicknames(flag=True)
        elif func_num == 19:
            if msg["message_type"] == "group":
                await self.bot_api.send_group_msg(group_id=msg["group_id"], message="正在重载昵称……")
            elif msg["message_type"] == "private":
                await self.bot_api.send_private_msg(user_id=msg["sender"]["user_id"], message="正在重载昵称……")
            reply = await self.reload_nickName()
        elif func_num >= 20:
            if func_num == 20:
                fix = self._pool["settings"]["default_pool"]
            elif func_num == 21:
                fix = "cn"
            elif func_num == 22:
                fix = "tw"
            elif func_num == 23:
                fix = "jp"
            reply = await self.thirtytimes(
                qqid=msg["sender"]["user_id"],
                nickname=msg["sender"]["card"],fix=fix)
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
