var vm = new Vue({
    el: '#app',
    data: {
        fullWidth: document.documentElement.clientWidth,
        tabPosition:'left',
        imgWidth:{width:'96px'},
        spanStyle:{
            fontSize: "12px",
            height: "18px",
            lineHeight: "18px"
        },
        bodyStyle:{
            padding:"15px 5px"
        },
        drawer:false,
        checkTop: false,
        settings: null,
        visible: false,
        star: 1,
        lang_cn: true,
        character:null,
        charNames:null,
        activePool:"pool_jp",
        poolName:{
            pool_jp:"日服卡池",
            pool_tw:"台服卡池",
            pool_cn:"国服卡池",
            others:"其他设置"
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
        pool_prop:null,
        inputVisible_1:false,
        inputValue_1:"",
        inputVisible_2:false,
        inputValue_2:"",
        inputVisible_3:false,
        inputValue_3:"",
        inputVisible_4:false,
        inputValue_4:"",
        inputVisible_5:false,
        inputValue_5:"",
    },
    mounted() {
        var thisvue = this;
        window.addEventListener('resize', this.handleResize)
        this.handleResize()
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.settings = res.data.settings;
                let char  = JSON.parse(JSON.stringify(res.data.settings.character))
                let character = {
                    pool_jp:{},
                    pool_tw:{},
                    pool_cn:{}
                }
                let charNames = {}
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
                                    prop = prop_/10
                                    let prop_last_ = thisvue.settings[suf]["pools"][star]["prop_last"]/thisvue.settings[suf]["pools"][star]["pool"].length
                                    prop_last = prop_last_/10
                                }else if(pickUp[star]["pool"] && Object.keys(pickUp[star]["pool"]).indexOf(char[type][star][id][1])!=-1){
                                    sel = true
                                    let prop_ = pickUp[star]["pool"][char[type][star][id][1]]["prop"]
                                    prop = prop_/10
                                    let prop_last_ = pickUp[star]["pool"][char[type][star][id][1]]["prop_last"]
                                    prop_last = prop_last_/10
                                    pick_up = true
                                    free_stone = pickUp[star]["pool"][char[type][star][id][1]]["free_stone"]
                                    sel_pick_up[suf][star][id]={
                                        prop:prop.toFixed(3),
                                        free_stone:free_stone
                                    }
                                }
                                prop = prop.toFixed(3)+"%"
                                prop_last = prop_last.toFixed(3)+"%"
                                character[suf][type][star][id]={
                                    id:id,
                                    name:char[type][star][id],
                                    sel:sel,
                                    prop:prop,
                                    prop_last:prop_last,
                                    pick_up:pick_up,
                                    free_stone:free_stone
                                }
                                if (!charNames[id]) {
                                    charNames[id]=char[type][star][id]
                                }
                            }
                        }
                    }
                }
                thisvue.character=character
                thisvue.sel_normal=sel_normal
                thisvue.sel_pick_up=sel_pick_up
                thisvue.pool_prop=pool_prop
                thisvue.charNames=charNames
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
    beforeDestroy(){
        window.removeEventListener('resize', this.handleResize)
    },
    methods: {
        handleResize:function(){
            this.fullWidth = document.documentElement.clientWidth
            if ( this.fullWidth > 800) {
                this.imgWidth.width="96px"
                this.checkTop = true
                this.spanStyle={
                    fontSize: "12px",
                    height: "18px",
                    lineHeight: "18px"
                }
                this.tabPosition="top"
                this.bodyStyle.padding="20px"
                this.poolName={
                    pool_jp:"日服卡池",
                    pool_tw:"台服卡池",
                    pool_cn:"国服卡池",
                    others:"其他设置"
                }
            }else{
                this.imgWidth.width="72px"
                this.checkTop = false
                this.spanStyle={
                    fontSize: "9px",
                    height: "16px",
                    lineHeight: "16px"
                }
                this.tabPosition="left"
                this.bodyStyle.padding="15px 5px"
                this.poolName={
                    pool_jp:"JP",
                    pool_tw:"TW",
                    pool_cn:"CN",
                    others:""
                }
            }
        },
        update: function () {
            for (let suf in this.poolName) {
                if (suf == "others") {
                    continue
                }
                let pools = {star1:{pool:[],prop:795,prop_last:0,name:"1星",prefix:"★"},star2:{pool:[],prop:180,prop_last:975,name:"2星",prefix:"★★"},star3:{pool:[],prop:25,prop_last:25,name:"3星",prefix:"★★★"}}
                for (let star in pools) {
                    for (let char of this.sel_normal[suf][star]) {
                        pools[star]["pool"].push(this.charNames[char][1])
                    }
                }
                if (Object.keys(this.sel_pick_up[suf].star3).length>0){
                    pools["pick_up"]={pool:[],prop:7,prop_last:7,name:"Pick Up",prefix:"★★★",free_stone:[]}
                    for (let char in this.sel_pick_up[suf].star3) {
                        pools["pick_up"]["pool"].push(this.charNames[char][1])
                        if (this.sel_pick_up[suf].star3[char]["free_stone"]) {
                            pools["pick_up"]["free_stone"].push(this.charNames[char][1])
                        }
                    }
                    pools.star3.prop-=7
                    pools.star3.prop_last-=7
                }
                if (Object.keys(this.sel_pick_up[suf].star2).length>0){
                    let char_s2 = {}
                    for (let char in this.sel_pick_up[suf].star2) {
                        if (!char_s2[this.sel_pick_up[suf].star2[char]["prop"] * 10]) {
                            char_s2[this.sel_pick_up[suf].star2[char]["prop"] * 10]=[]
                        }
                        char_s2[this.sel_pick_up[suf].star2[char]["prop"] * 10].push(this.charNames[char][1])
                    }
                    let i = 1;
                    for (let k in char_s2) {
                        pools["pick_up"+i]={pool:char_s2[k],prop:Number(k),prop_last:k*5.4,name:"Pick Up",prefix:"★★",free_stone:[]}
                        i++
                    }
                    pools.star2.prop-=50
                    pools.star2.prop_last-=270
                }
                this.settings[suf]["pools"]=pools
            }
            this.settings.info.ver=this.getDateNow()
            axios.put(api_path, {
                setting: this.settings,
                csrf_token: csrf_token,
            }).then(function (res) {
                if (res.data.code == 0) {
                    vm.$message.success('设置成功，重启后生效');
                } else {
                    vm.$message.warnning('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                vm.$message.error(error);
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
                return this.sel_pick_up[n][n1][id]["prop"]+"%"
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
                    this.handlePickProp(n,type,n1,n2)
                }else{
                    let inx = this.sel_normal[n][n1].indexOf(n2)
                    this.sel_normal[n][n1].splice(inx,1)
                }
            }else{
                this.sel_normal[n][n1].push(n2)
            }
        },
        togglePickCheck:function (n,type,n1,n2) {
            let prop = 0
            let flag = false
            if (n1 == "star2" && !this.character[n][type][n1][n2]["pick_up"]) {
                let keys = Object.keys(this.sel_pick_up[n][n1])
                if (keys.length >= 1) {
                    flag = true
                    prop = 5/(keys.length+1)
                    vm.$prompt('请输入概率:', '提示', {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        inputValue:prop.toFixed(3),
                        inputValidator:function(e){
                            if (/[0-9]*[\.]{1}[0-9]{3}/.test(e)) {
                                if (Number(e) - 5 < 0 && Number(e) > 0) {
                                    return true
                                }
                            }
                        return "请输入大于0,小于5的三位小数"
                        }
                    }).then(({ value }) => {
                        prop = value
                        this.togglePick(n,type,n1,n2,prop)
                    }).catch(() => {
                        return
                    });
                }
            }
            if(!flag){
                this.togglePick(n,type,n1,n2,prop)
            }
        },
        togglePick:function(n,type,n1,n2,prop){
            this.character[n][type][n1][n2]["pick_up"]=!this.character[n][type][n1][n2]["pick_up"]
            if (!this.character[n][type][n1][n2]["pick_up"]){
                this.sel_normal[n][n1].push(n2)
                this.character[n][type][n1][n2]["prop"] = Number(this.sel_pick_up[n][n1][n2]["prop"]).toFixed(3)+"%"
                this.character[n][type][n1][n2]["free_stone"] = false
                delete this.sel_pick_up[n][n1][n2]
            }else{
                let inx = (this.sel_normal[n][n1]).indexOf(n2)
                this.sel_normal[n][n1].splice(inx,1)
                if (prop == 0) {
                    this.sel_pick_up[n][n1][n2]={prop:0,free_stone:false}
                }else{
                    this.sel_pick_up[n][n1][n2]={prop:prop,free_stone:false}
                }
                this.character[n][type][n1][n2]["prop"] = Number(this.sel_pick_up[n][n1][n2]["prop"]).toFixed(3)+"%"
            }
            this.handlePickProp(n,type,n1,n2)
        },
        handlePickProp:function (n,type,n1,n2) {
            if(n1=="star3"){
                let prop = (7/Object.keys(this.sel_pick_up[n][n1]).length/10).toFixed(3)
                for (let k of Object.keys(this.sel_pick_up[n][n1])) {
                    this.sel_pick_up[n][n1][k]["prop"]=prop
                }
                this.character[n][type][n1][n2]["prop"]=prop+"%"
            }else if(n1=="star2"){
                let prop_in = 0
                let pick_up = this.character[n][type][n1][n2]["pick_up"]
                let keys = Object.keys(this.sel_pick_up[n][n1]);
                if (pick_up) {
                    if (keys.length==1){
                        prop_in = "5.000"
                    }else{
                        prop_in = this.sel_pick_up[n][n1][n2]["prop"]
                    }
                }else{
                    prop_in = 0
                }
                let prop_a = 5
                if (!pick_up){
                    prop_a = 0
                    for (let e of keys) {
                        prop_a += Number(this.sel_pick_up[n][n1][e]["prop"].substr(0,5))
                    }
                }
                for (let k of keys) {
                    if (k != n2) {
                        let prop_pre = Number(this.sel_pick_up[n][n1][k]["prop"].substr(0,5))
                        let per = prop_pre/prop_a
                        let prop_o = Number(5-prop_in)*per
                        this.sel_pick_up[n][n1][k]["prop"]=Number(prop_o).toFixed(3)
                    }
                }
                if (pick_up) {
                    this.sel_pick_up[n][n1][n2]["prop"]=prop_in
                    this.character[n][type][n1][n2]["prop"]=prop_in+"%"
                }

            }
        },
        toggleFreeSt(n,type,n1,n2){
            this.sel_pick_up[n][n1][n2]["free_stone"]=!this.sel_pick_up[n][n1][n2]["free_stone"]
            this.character[n][type][n1][n2]["free_stone"]=!this.character[n][type][n1][n2]["free_stone"]
        },
        getDateNow(){
            let date = new Date()
            let res = (date.getFullYear())*100000000+(date.getMonth()+1)*1000000+(date.getDate()*10000+date.getHours()*100+date.getMinutes())
            return res
        },
        showInput(key){
            this['inputVisible_'+key]=true
            this.$nextTick(_ => {
              this.$refs['saveTagInput_'+key].$refs.input.focus();
            });
        },
        inputConfirm(key,index){
            let inputValue = this['inputValue_'+index]
            if(inputValue!=''){
                this.settings["replys"][key]["reply"].push(inputValue)
            }
            this['inputVisible_'+index]=false
            this['inputValue_'+index]=""
        },
        closeReplaysTag(key,i){
            this.settings["replys"][key]["reply"].splice(i,1)
        }
    },
    delimiters: ['[[', ']]'],
})