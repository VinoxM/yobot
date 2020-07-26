var vm = new Vue({
    el: '#app',
    data: {
        settings: null,
        visible: false,
        star: 1,
        lang_cn: true,
        character:null,
        activePool:"pool_jp",
        poolName:{
            pool_jp:"日服卡池",
            pool_tw:"台服卡池",
            pool_cn:"国服卡池"
        },
        poolTitle:{
            star3:"SSR",
            star2:"SR",
            star1:"R",
            hidden:"Hidden",
        },
        activeStars:{
            pool_jp:["star3"],
            pool_tw:["star3"],
            pool_cn:["star3"]
        },
        nickName_on:false,
        prop_on:false,
        hidden_unsel:false,
        prop:{
            star1:795,
            star2:180,
            star3:25
        },
        sel_normal:null,
        sel_pick_up:null,
        pool_prop:null
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.settings = res.data.settings;
                let char  = JSON.parse(JSON.stringify(res.data.settings.character))
                let character = {
                    pool_jp:{},
                    pool_tw:{},
                    pool_cn:{}
                }
                let sel_normal = {
                    pool_jp:{star1:[],star2:[],star3:[]},
                    pool_tw:{star1:[],star2:[],star3:[]},
                    pool_cn:{star1:[],star2:[],star3:[]}
                }
                let sel_pick_up = {
                    pool_jp:{star1:{},star2:{},star3:{}},
                    pool_tw:{star1:{},star2:{},star3:{}},
                    pool_cn:{star1:{},star2:{},star3:{}}
                }
                let pool_prop = {
                    pool_jp:{star1:0,star2:0,star3:0},
                    pool_tw:{star1:0,star2:0,star3:0},
                    pool_cn:{star1:0,star2:0,star3:0}
                }
                for (let suf in character) {
                    let pickUp = {
                        star1:{
                            pool: {}
                        },
                        star2:{
                            pool:{}
                        },
                        star3:{
                            pool:{}
                        },
                    }
                    character[suf]=JSON.parse(JSON.stringify(char))
                    for (let type in thisvue.settings[suf]["pools"]){
                        if (type.length > 6) {
                            let pu = thisvue.settings[suf]["pools"][type]
                            let c = String(pu['prefix']).split("★").length-1
                            for (let i = 0; i < pu["pool"].length; i++) {
                                pickUp["star"+c]["pool"][pu["pool"][i]]={
                                    prop:pu["prop"]/pu["pool"].length,
                                    prop_last:pu["prop_last"]/pu["pool"].length,
                                    free_stone: pu["free_stone"].indexOf(pu["pool"][i])!=-1
                                }
                            }
                        }
                    }
                    for (let type in char) {
                        for (let star in char[type]) {
                            for (let id in char[type][star]) {
                                pool_prop[suf][star]=thisvue.settings[suf]["pools"][star]["prop"]
                                let sel = false
                                let prop = 0
                                let prop_last = 0
                                let pick_up = false
                                let free_stone = false
                                if (thisvue.settings[suf]["pools"][star]["pool"].indexOf(char[type][star][id][1]) != -1) {
                                    sel = true
                                    sel_normal[suf][star].push(id)
                                    let prop_ = thisvue.settings[suf]["pools"][star]["prop"]/thisvue.settings[suf]["pools"][star]["pool"].length
                                    prop = (prop_/10).toFixed(3)+"%"
                                    let prop_last_ = thisvue.settings[suf]["pools"][star]["prop_last"]/thisvue.settings[suf]["pools"][star]["pool"].length
                                    prop_last = (prop_last_/10).toFixed(3)+"%"
                                }else if(pickUp[star]["pool"] && Object.keys(pickUp[star]["pool"]).indexOf(char[type][star][id][1])!=-1){
                                    sel = true
                                    let prop_ = pickUp[star]["pool"][char[type][star][id][1]]["prop"]
                                    prop = (prop_/10).toFixed(3)+"%"
                                    sel_pick_up[suf][star][id]=prop
                                    let prop_last_ = pickUp[star]["pool"][char[type][star][id][1]]["prop_last"]
                                    prop_last = (prop_last_/10).toFixed(3)+"%"
                                    pick_up = true
                                    free_stone = pickUp[star]["pool"][char[type][star][id][1]]["free_stone"]
                                }
                                character[suf][type][star][id]={
                                    id:id,
                                    name:char[type][star][id],
                                    sel:sel,
                                    prop:prop,
                                    prop_last:prop_last,
                                    pick_up:pick_up,
                                    free_stone:free_stone
                                }
                            }
                        }
                    }
                }
                thisvue.character=character
                thisvue.sel_normal=sel_normal
                thisvue.sel_pick_up=sel_pick_up
                thisvue.pool_prop=pool_prop
            } else {
                vm.$message.warning('加载数据错误:'+res.data.message);
            }
        })
        //     .catch(function (error) {
        //     vm.$message.error('加载数据错误:'+error);
        // });
    },
    computed:{
        suf(){
            return this.star<3?1:3
        },
        lang(){
            return this.lang_cn?1:0
        }
    },
    watch:{

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
        },
        prop_computed:function (sel,pick,n,n1,prop,id) {
            if (!sel){
                return "0.000%"
            }
            if (pick) {
                return this.sel_pick_up[n][n1][id]
            }else{
                return (this.pool_prop[n][n1]/this.sel_normal[n][n1].length/10).toFixed(3)+'%'
            }
        },
        toggleSel:function (n,type,n1,n2) {
            this.character[n][type][n1][n2]["sel"]=!this.character[n][type][n1][n2]["sel"]
            if (!this.character[n][type][n1][n2]["sel"]){
                if (this.character[n][type][n1][n2]["pick_up"]) {
                    this.character[n][type][n1][n2]["pick_up"]=false
                    delete this.sel_pick_up[n][n1][n2]
                    this.handlePickProp(n,type,n1,n2,n1)
                }else{
                    let inx = this.sel_normal[n][n1].indexOf(this.sel_normal[n][n1][n2])
                    this.sel_normal[n][n1].splice(inx,1)
                }
            }else{
                this.sel_normal[n][n1].push(n2)
            }
        },
        togglePick:function (n,type,n1,n2) {
            this.character[n][type][n1][n2]["pick_up"]=!this.character[n][type][n1][n2]["pick_up"]
            if (!this.character[n][type][n1][n2]["pick_up"]){
                this.sel_normal[n][n1].push(n2)
                delete this.sel_pick_up[n][n1][n2]
            }else{
                let inx = this.sel_normal[n][n1].indexOf(this.sel_normal[n][n1][n2])
                this.sel_normal[n][n1].splice(inx,1)
                this.sel_pick_up[n][n1][n2]=0
            }
            this.handlePickProp(n,type,n1,n2,n1)
        },
        handlePickProp:function (n,type,n1,n2,star) {
            let prop_=0
            switch (star) {
                case "star3":
                    prop_ = 7
                    break
                case "star2":
                    prop_ = 50
                    break
            }
            let prop = (prop_/Object.keys(this.sel_pick_up[n][n1]).length/10).toFixed(3)+"%"
            for (let k of Object.keys(this.sel_pick_up[n][n1])) {
                this.sel_pick_up[n][n1][k]=prop
            }
            this.character[n][type][n1][n2]["prop"]=prop
        }
    },
    delimiters: ['[[', ']]'],
})