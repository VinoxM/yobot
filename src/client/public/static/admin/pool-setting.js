var vm = new Vue({
    el: '#app',
    data: {
        settings: null,
        visible: false,
        star: 1,
        lang_cn: true,
        character:{},
        activePool:"jp"
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.settings = res.data.settings;
                let char  = JSON.parse(JSON.stringify(res.data.settings.character))
                let char_jp = JSON.parse(JSON.stringify(char))
                for (let type in char) {
                    for (let star in char[type]) {
                        for (let id in char[type][star]) {
                            console.log(star)
                            // char_jp[type][star][id]={
                            //     id:id,
                            //     name:char[type][star][id],
                            //     sel:thisvue.settings["pool_jp"]["pools"][star]["pool"].indexOf(char[type][star][id][1])!=-1
                            // }
                        }
                    }
                }
                thisvue.character=char
                console.log(char_jp)
            } else {
                vm.$message.warning('加载数据错误:'+res.data.message);
            }
        }).catch(function (error) {
            vm.$message.error('加载数据错误:'+error);
        });
    },
    computed:{
        suf(){
            return this.star<3?1:3
        },
        lang(){
            return this.lang_cn?1:0
        }
    },
    methods: {
        addpool: function () {
            let newname = "奖池" + (Object.keys(this.settings.pool).length+1);
            this.$set(this.settings.pool, newname, {
                prop: 0,
                prop_last: 0,
                prefix: "★★★",
                pool: ["请输入内容"],
            });
        },
        update: function () {
            var thisvue = this;
            axios.put(api_path, {
                setting: thisvue.settings,
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    alert('设置成功，重启后生效');
                } else {
                    alert('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                alert(error);
            });
        },
        editPools: function (star) {
            this.star=star
            this.visible=true
        }
    },
    delimiters: ['[[', ']]'],
})