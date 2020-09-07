var vm = new Vue({
    el: '#app',
    data: {
        list:[123,1234,1235],
        setting: {},
        activeName:"0",
        activeNames: [],
        bossSetting: false,
        domain: '',
        domainApply: false,
        applyName: '',
        loading: false,
        tabActive:"1",
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
        inputVisible_6:false,
        inputValue_6:"",
        inputVisible_7:false,
        inputValue_7:"",
        inputVisible_filter:[],
        inputValue_filter:[],
        inputVisible_replace:[],
        inputValue_replace:[],
        inputVisible_result:[],
        inputValue_result:[],
        fileType:{
            Picture:{suffix:[".jpg",".jpeg",".png"],className:"el-icon-picture-outline",action:"view"},
        },
        fileData:[],
        curFilePath:"",
        filePaths:[""],
        viewVisible:false,
        viewTitle:"",
        viewSuffix:"",
        viewSrc:"",
        addVisible:false,
        addFolder:1,
        folderName:""
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code == 0) {
                thisvue.setting = res.data.settings;
                for (let i = 0; i < thisvue.setting['extra'].length; i++) {
                    thisvue.inputVisible_filter.push(false)
                    thisvue.inputValue_filter.push("")
                    thisvue.inputVisible_replace.push(false)
                    thisvue.inputValue_replace.push("")
                    thisvue.inputVisible_result.push(false)
                    thisvue.inputValue_result.push("")
                }
            } else {
                vm.$message.warning(res.data.message);
            }
        }).catch(function (error) {
            vm.$message.error(error);
        });
    },
    watch:{
       tabActive(newVal,oldVal){
           console.log(newVal)
           if (newVal==='4'){
               this.getFileByPath("","this")
           }
       }
    },
    methods: {
        update: function (event) {
            this.setting.web_mode_hint = false;
            axios.put(
                api_path,
                {
                    setting: this.setting,
                    csrf_token: csrf_token,
                },
            ).then(function (res) {
                if (res.data.code == 0) {
                    vm.$message.success('设置成功，重启机器人后生效');
                } else {
                    vm.$message.warning('设置失败：' + res.data.message);
                }
            }).catch(function (error) {
                vm.$message.error(error);
            });
        },
        sendApply: function (api) {
            if (this.domain === '') {
                vm.$message.warning('请选择后缀');
                return;
            }
            if (/^[0-9a-z]{1,16}$/.test(this.applyName)) {
                ;
            } else {
                vm.$message.warning('只能包含字母、数字');
                return;
            }
            var thisvue = this;
            this.loading = true;
            axios.get(
                api + '?name=' + thisvue.applyName + thisvue.domain
            ).then(function (res) {
                thisvue.domainApply = false;
                if (res.data.code == 0) {
                    vm.$message.success('申请成功，请等待1分钟左右解析生效');
                    thisvue.setting.public_address = thisvue.setting.public_address.replace(/\/\/([^:\/]+)/, '//' + thisvue.applyName + thisvue.domain);
                    thisvue.update(null);
                } else if (res.data.code == 1) {
                    vm.$message.warning('申请失败，此域已被占用');
                } else {
                    vm.$message.warning('申请失败，' + res.data.message);
                }
                thisvue.loading = false;
            }).catch(function (error) {
                thisvue.loading = false;
                vm.$message.error(error);
            });
        },
        switch_levels: function (area) {
            if (this.setting.boss[area].length <= 3) {
                this.setting.boss[area].push([0, 0, 0, 0, 0]);
            } else {
                this.setting.boss[area].pop();
            }
        },
        comfirm_change_clan_mode: function (event) {
            this.$alert('修改模式后，公会战数据会重置。请不要在公会战期间修改！', '警告', {
                confirmButtonText: '知道了',
                type: 'warning',
            });
        },
        closeTag:function(key,index){
            this.setting[key].splice(index,1)
        },
        inputConfirm:function(key,index){
            let inputValue = this['inputValue_'+index]
            if(inputValue!=''){
                this.setting[key].push(inputValue)
            }
            this['inputVisible_'+index]=false
            this['inputValue_'+index]=""
        },
        showInput:function(key,e){
            this['inputVisible_'+key]=true
            this.$nextTick(_ => {
              this.$refs['saveTagInput_'+key].$refs.input.focus();
            });
        },
        closeTag2:function(key,index,index1){
            this.setting.extra[index][key].splice(index1,1)
        },
        inputConfirm2:function(key,index,index1){
            let inputValue = this['inputValue_'+key][index]
            if(inputValue!=''){
                switch (key) {
                    case "replace":
                        if ( /^[^,]+[,]{1}[^,]+$/.test(inputValue)){
                            this.setting.extra[index][key+"_"].push(inputValue.split(','))
                        }
                        break;
                    case "result":
                        let f = true
                        switch (inputValue) {
                            case 'result':
                                if (this.setting.extra[index][key + "_"].indexOf('result') != -1) {
                                    f=false
                                }
                                break;
                            case 'record':
                                if (this.setting.extra[index][key + "_"].indexOf('record') != -1){
                                    f=false
                                }
                                break;
                        }
                        if (!f){
                            break;
                        }
                    default:
                        this.setting.extra[index][key+"_"].push(inputValue)
                        break;
                }
            }
            this['inputVisible_'+key].splice(index,1,false)
            this['inputValue_'+key].splice(index,1,"")
        },
        showInput2:function(key,index){
            this['inputVisible_'+key].splice(index,1,true)
            this.$nextTick(_ => {
              this.$refs['saveTagInput_'+key][0].$refs.input.focus();
            });
        },
        extraAdd:function () {
            this.setting.extra.push(
                {
                    title:"",
                    on:true,
                    prefix:true,
                    full_keyword: true,
                    keyword:"",
                    filter_on:false,
                    filter_:[],
                    replace_on:false,
                    replace_:[],
                    result_on:true,
                    result_:[],
                    record_folder: ""
                }
            )
            this.inputVisible_filter.push(false)
            this.inputValue_filter.push("")
            this.inputVisible_replace.push(false)
            this.inputValue_replace.push("")
            this.inputVisible_result.push(false)
            this.inputValue_result.push("")
        },
        extraDel:function(k){
            this.setting.extra.splice(k,1)
            this.inputVisible_filter.splice(k,1)
            this.inputValue_filter.splice(k,1)
            this.inputVisible_replace.splice(k,1)
            this.inputValue_replace.splice(k,1)
            this.inputVisible_result.splice(k,1)
            this.inputValue_result.splice(k,1)
        },
        getFileByPath(d,action){
            let path = d['fileName']
            switch (action) {
                case "none":
                    return
                case "next":
                    this.curFilePath+="\\"+path
                    this.filePaths=this.curFilePath.split("\\")
                    break
                case "pre":
                    if (this.filePaths.length===1) return
                    let paths = this.curFilePath.split("\\")
                    paths.splice(paths.length-1,1)
                    this.curFilePath=paths.join("\\")
                    this.filePaths=paths
                    break
                case "click":
                    this.curFilePath=path
                    break
                case "view":
                    let fileType=d['fileType']
                    this.viewTitle=path.replace(fileType,"")
                    this.viewSuffix=fileType
                    this.viewSrc="/yobot/file/view"+this.curFilePath+"/"+path
                    this.viewVisible=true
                    break
            }
            axios.post("/yobot/admin/setting/filepath",{path:this.curFilePath,csrf_token:csrf_token})
            .then((res)=>{
                let data = res.data["files"]
                for (let d of data) {
                    let fileSuffix=d['fileSuffix']
                    if (fileSuffix&&fileSuffix!==""){
                        let flag = false
                        for (let key in this.fileType) {
                            if (this.fileType[key].suffix.indexOf(fileSuffix)>-1){
                                d['fileType']=key
                                d['action']=this.fileType[key]["action"]
                                d['className']=this.fileType[key]["className"]
                                flag = true
                                break
                            }
                        }
                        if (!flag){
                            d['fileType']="Document"
                            d['action']="none"
                            d['className']="el-icon-document"
                        }
                    }else{
                        d['fileType']="Folder"
                        d['action']="next"
                        d['className']="el-icon-folder"
                    }
                }
                this.fileData=data
            })
        },
        changePath(key){
            let path = ""
            this.filePaths=this.filePaths.slice(0,key+1)
            if (key>0){
                path = this.filePaths.join("\\")
            }
            this.getFileByPath({fileName:path},"click")
        }
    },
    delimiters: ['[[', ']]'],
})