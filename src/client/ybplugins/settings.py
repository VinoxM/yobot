import json
import os
from urllib.parse import urljoin

from quart import Quart, jsonify, redirect, request, session, url_for, send_file

from .templating import render_template
from .ybdata import User, Clan_group


class Setting:
    Passive = False
    Active = False
    Request = True

    def __init__(self,
                 glo_setting,
                 bot_api,
                 *args, **kwargs):
        self.setting = glo_setting
        self.base_file_path = self.setting.get("base_file_path", "F:\\Documents")

    def register_routes(self, app: Quart):

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/'),
            methods=['GET'])
        async def yobot_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group > 10:
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=user.authority_group,
                )
            return await render_template(
                'admin/setting.html',
            )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/api/'),
            methods=['GET', 'PUT'])
        async def yobot_setting_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            if request.method == 'GET':
                settings = self.setting.copy()
                del settings['dirname']
                del settings['verinfo']
                del settings['host']
                del settings['port']
                del settings['access_token']
                return jsonify(
                    code=0,
                    message='success',
                    settings=settings,
                )
            elif request.method == 'PUT':
                req = await request.get_json()
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                new_setting = req.get('setting')
                if new_setting is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                self.setting.update(new_setting)
                save_setting = self.setting.copy()
                del save_setting['dirname']
                del save_setting['verinfo']
                config_path = os.path.join(
                    self.setting['dirname'], 'yobot_config.json')
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(save_setting, f, ensure_ascii=False, indent=4)
                return jsonify(
                    code=0,
                    message='success',
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/pool-setting/'),
            methods=['GET'])
        async def yobot_pool_setting():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=user.authority_group,
                )
            return await render_template('admin/pool-setting.html')

        @app.route(
            urljoin(self.setting['public_basepath'],
                    'admin/pool-setting/api/'),
            methods=['GET', 'PUT'])
        async def yobot_pool_setting_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            if request.method == 'GET':
                with open(os.path.join(self.setting['dirname'], 'pool3.json'),
                          'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify(
                    code=0,
                    message='success',
                    settings=settings,
                )
            elif request.method == 'PUT':
                req = await request.get_json()
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                new_setting = req.get('setting')
                if new_setting is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                with open(os.path.join(self.setting['dirname'], 'pool3.json'),
                          'w', encoding='utf-8') as f:
                    json.dump(new_setting, f, ensure_ascii=False, indent=2)
                return jsonify(
                    code=0,
                    message='success',
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/users/'),
            methods=['GET'])
        async def yobot_users_managing():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=user.authority_group,
                )
            return await render_template('admin/users.html')

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/users/api/'),
            methods=['POST'])
        async def yobot_users_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            try:
                req = await request.get_json()
                if req is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = req['action']
                if action == 'get_data':
                    users = []
                    for user in User.select().where(
                            User.deleted == False,
                    ):
                        users.append({
                            'qqid': user.qqid,
                            'nickname': user.nickname,
                            'clan_group_id': user.clan_group_id,
                            'authority_group': user.authority_group,
                            'last_login_time': user.last_login_time,
                            'last_login_ipaddr': user.last_login_ipaddr,
                        })
                    return jsonify(code=0, data=users)
                elif action == 'modify_user':
                    data = req['data']
                    m_user: User = User.get_or_none(qqid=data['qqid'])
                    if ((m_user.authority_group <= user.authority_group) or
                            (data.get('authority_group', 999)) <= user.authority_group):
                        return jsonify(code=12, message='Exceed authorization is not allowed')
                    if data.get('authority_group') == 1:
                        self.setting['super-admin'].append(ctx['user_id'])
                        save_setting = self.setting.copy()
                        del save_setting['dirname']
                        del save_setting['verinfo']
                        config_path = os.path.join(
                            self.setting['dirname'], 'yobot_config.json')
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(save_setting, f, indent=4)
                    if m_user is None:
                        return jsonify(code=21, message='user not exist')
                    for key in data.keys():
                        setattr(m_user, key, data[key])
                    m_user.save()
                    return jsonify(code=0, message='success')
                elif action == 'delete_user':
                    user = User.get_or_none(qqid=req['data']['qqid'])
                    if user is None:
                        return jsonify(code=21, message='user not exist')
                    user.clan_group_id = None
                    user.authority_group = 999
                    user.password = None
                    user.deleted = True
                    user.save()
                    return jsonify(code=0, message='success')
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                return jsonify(code=31, message=str(e))

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/groups/'),
            methods=['GET'])
        async def yobot_groups_managing():
            if 'yobot_user' not in session:
                return redirect(url_for('yobot_login', callback=request.path))
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return await render_template(
                    'unauthorized.html',
                    limit='主人',
                    uath=user.authority_group,
                )
            return await render_template('admin/groups.html')

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/groups/api/'),
            methods=['POST'])
        async def yobot_groups_api():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 10:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            try:
                req = await request.get_json()
                if req is None:
                    return jsonify(
                        code=30,
                        message='Invalid payload',
                    )
                if req.get('csrf_token') != session['csrf_token']:
                    return jsonify(
                        code=15,
                        message='Invalid csrf_token',
                    )
                action = req['action']
                if action == 'get_data':
                    groups = []
                    for group in Clan_group.select().where(
                            Clan_group.deleted == False,
                    ):
                        groups.append({
                            'group_id': group.group_id,
                            'group_name': group.group_name,
                            'game_server': group.game_server,
                        })
                    return jsonify(code=0, data=groups)
                if action == 'drop_group':
                    User.update({
                        User.clan_group_id: None,
                    }).where(
                        User.clan_group_id == req['group_id'],
                    ).execute()
                    Clan_group.delete().where(
                        Clan_group.group_id == req['group_id'],
                    ).execute()
                    return jsonify(code=0, message='ok')
                else:
                    return jsonify(code=32, message='unknown action')
            except KeyError as e:
                return jsonify(code=31, message=str(e))

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/filepath/'),
            methods=['POST'])
        async def yobot_setting_filepath():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            req = await request.get_json()
            if req.get('csrf_token') != session['csrf_token']:
                return jsonify(
                    code=15,
                    message='Invalid csrf_token',
                )
            if request.method == 'POST':
                base_path = self.base_file_path
                file_path = req.get('path')
                path = base_path + file_path
                files = os.listdir(path)
                res = []
                for f in files:
                    res.append(
                        {"fileName": f, "isDir": os.path.isdir(path + "\\" + f), "fileSuffix": os.path.splitext(f)[1]})
                return jsonify(
                    code=0,
                    message='success',
                    files=res
                )

        @app.route(
            urljoin(self.setting['public_basepath'], 'admin/setting/file/delete'),
            methods=['POST'])
        async def yobot_setting_file_del():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            req = await request.get_json()
            if req.get('csrf_token') != session['csrf_token']:
                return jsonify(
                    code=15,
                    message='Invalid csrf_token',
                )
            path = req.get("path")
            if path.startswith("\\"):
                path = path[1:]
            file_path = req.get("file_name")
            base_path = self.base_file_path
            del_path = os.path.join(base_path, path, file_path)
            if os.path.isdir(del_path):
                if len(os.listdir(del_path)) > 0:
                    return jsonify(
                        code=500,
                        message="You can only delete empty folders"
                    )
                else:
                    os.rmdir(del_path)
                    return jsonify(
                        code=0,
                        message="Delete Folder success"
                    )
            else:
                if os.path.exists(del_path):
                    os.remove(del_path)
                    return jsonify(
                        code=0,
                        message="Delete document success"
                    )
                else:
                    return jsonify(
                        code=500,
                        message="Documents is not exists"
                    )

        @app.route(
            urljoin(self.setting["public_basepath"],
                    "admin/setting/file/view/<path:filename>"),
            methods=["GET"])
        async def file_view(filename):
            local_file = os.path.join(self.base_file_path, filename)
            return await send_file(local_file)

        @app.route(
            urljoin(self.setting["public_basepath"],
                    "admin/setting/file/upload.<path:filepath>"),
            methods=["POST"])
        async def file_upload(filepath):
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            req = request.args
            if req.get('csrf_token') != session['csrf_token']:
                return jsonify(
                    code=15,
                    message='Invalid csrf_token',
                )
            if not str(filepath).startswith("root"):
                return
            save_path = os.path.join(self.base_file_path, str(filepath)[5:].replace("/", "\\"))
            files = await request.files
            for file in files.values():
                file_name = file.filename
                with open(os.path.join(save_path, file_name), 'wb') as f:
                    f.write(file.stream.read())
            return jsonify(code=0, message='Upload success')

        @app.route(
            urljoin(self.setting["public_basepath"],
                    "admin/setting/file/folder/"),
            methods=["POST"])
        async def file_create_folder():
            if 'yobot_user' not in session:
                return jsonify(
                    code=10,
                    message='Not logged in',
                )
            user = User.get_by_id(session['yobot_user'])
            if user.authority_group >= 100:
                return jsonify(
                    code=11,
                    message='Insufficient authority',
                )
            req = await request.get_json()
            if req.get('csrf_token') != session['csrf_token']:
                return jsonify(
                    code=15,
                    message='Invalid csrf_token',
                )
            file_path = req.get("path")
            folder_name = req.get("folderName")
            save_path = os.path.join(self.base_file_path, file_path, folder_name)
            if os.path.isdir(save_path):
                return jsonify(code=500, message="Folder already exists")
            else:
                os.mkdir(save_path)
                return jsonify(code=0, message="Folder create success")
