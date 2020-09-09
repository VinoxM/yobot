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
        inputVisible_tri_msg:[],
        inputValue_tri_msg:[],
        inputVisible_tri_group:[],
        inputValue_tri_group:[],
        activeName_trigger:"",
        tableLoading:true,
        fileType:{
            Picture:{suffix:[".jpg",".jpeg",".png"],className:"el-icon-picture-outline",action:"view"},
            Record:{suffix:[".ogg",".mp3"],className:"el-icon-headset",action:"record"},
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
        folderName:"",
        fileList:[],
        recordVisible:false,
        recordTitle:"",
        recordSuffix:"",
        recordSrc:"",
        recordType:"",
        triggerTimer:{
            year:{
                flag:[],
                label:"年"
            },
            month:{
                flag:[],
                label:"月"
            },
            day:{
                flag:[],
                label:"日"
            },
            week:{
                flag:[],
                label:"周"
            },
            day_of_week:{
                flag:[],
                label:"星期"
            },
            hour:{
                flag:[],
                label:"时"
            },
            minute:{
                flag:[],
                label:"分"
            },
            second:{
                flag:[],
                label:"秒"
            },
            jitter:{
                flag:[],
                label:"延迟"
            },
        },
        renameVisible:false,
        renameFile:{
            oldFileName:"",
            newFileName:"",
            fileSuffix:""
        }
    },
    mounted() {
        var thisvue = this;
        axios.get(api_path).then(function (res) {
            if (res.data.code === 0) {
                thisvue.setting = res.data.settings;
                for (let i = 0; i < thisvue.setting['extra'].length; i++) {
                    thisvue.inputVisible_filter.push(false)
                    thisvue.inputValue_filter.push("")
                    thisvue.inputVisible_replace.push(false)
                    thisvue.inputValue_replace.push("")
                    thisvue.inputVisible_result.push(false)
                    thisvue.inputValue_result.push("")
                }
                for (let i = 0; i < thisvue.setting['trigger'].length; i++){
                    let tri = thisvue.setting['trigger'][i]
                    let triTimer = thisvue.triggerTimer
                    for (let k in triTimer) {
                        if (k==='jitter'){
                            triTimer[k].flag.push(tri[k]!==0)
                            continue
                        }
                        triTimer[k].flag.push(tri[k]!=='*')
                    }
                    thisvue.inputVisible_tri_msg.push(false)
                    thisvue.inputValue_tri_msg.push("")
                    thisvue.inputVisible_tri_group.push(false)
                    thisvue.inputValue_tri_group.push("")
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
           if (newVal==='9'){
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
                if (res.data.code === 0) {
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
                if (res.data.code === 0) {
                    vm.$message.success('申请成功，请等待1分钟左右解析生效');
                    thisvue.setting.public_address = thisvue.setting.public_address.replace(/\/\/([^:\/]+)/, '//' + thisvue.applyName + thisvue.domain);
                    thisvue.update(null);
                } else if (res.data.code === 1) {
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
        closeTag3:function(key,index,index1){
            this.setting.trigger[index][key].splice(index1,1)
        },
        inputConfirm3:function(key,key1,index){
            let inputValue = this['inputValue_'+key][index]
            if(inputValue !==""){
                this.setting.trigger[index][key1].push(inputValue)
            }
            this['inputVisible_'+key].splice(index,1,false)
            this['inputValue_'+key].splice(index,1,"")
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
        triggerAdd:function(){
            this.setting.trigger.push(
                {
                    on: true,
                    title: "",
                    year: "*",
                    month: "*",
                    day: "*",
                    week: "*",
                    day_of_week: "*",
                    hour: "*",
                    minute: "*",
                    second: "*",
                    jitter: 0,
                    msg: [],
                    img_on: true,
                    img_path: "",
                    groups: [],
                    label: "",
                }
            )
            for (let k in this.triggerTimer) {
                this.triggerTimer[k].flag.push(false)
            }
            this.inputVisible_tri_msg.push(false)
            this.inputValue_tri_msg.push("")
            this.inputVisible_tri_group.push(false)
            this.inputValue_tri_group.push("")
        },
        triggerDel:function(k){
            for (let key in this.triggerTimer) {
                this.triggerTimer[key].flag.splice(k,1)
            }
            this.setting.trigger.splice(k,1)
            this.inputVisible_tri_msg.splice(k,1)
            this.inputValue_tri_msg.splice(k,1)
            this.inputVisible_tri_group.splice(k,1)
            this.inputValue_tri_group.splice(k,1)
        },
        getFileByPath(d,action){
            this.tableLoading=true
            let path = d['fileName']
            let fileType=d['fileType'];
            let fileSuffix=d['fileSuffix']
            switch (action) {
                case "none":
                    this.tableLoading=false
                    return
                case "next":
                    this.curFilePath+="\\"+path
                    this.filePaths=this.curFilePath.split("\\")
                    break
                case "pre":
                    if (this.filePaths.length===1) {
                        this.tableLoading=false
                        return
                    }
                    let paths = this.curFilePath.split("\\")
                    paths.splice(paths.length-1,1)
                    this.curFilePath=paths.join("\\")
                    this.filePaths=paths
                    break
                case "click":
                    this.curFilePath=path
                    break
                case "view":
                    this.viewTitle=path.replace(fileSuffix,"")
                    this.viewSuffix=fileSuffix
                    this.viewSrc="/yobot/admin/setting/file/view"+this.curFilePath+"/"+path
                    this.viewVisible=true
                    this.tableLoading=false
                    return
                case "record":
                    this.recordTitle=path.replace(fileSuffix,"")
                    this.recordSuffix=fileSuffix
                    this.recordType="audio/"+fileSuffix.replace(".","")
                    this.recordSrc="/yobot/admin/setting/file/view"+this.curFilePath+"/"+path
                    this.recordVisible=true
                    this.tableLoading=false
                    return
            }
            axios.post("/yobot/admin/setting/filepath",{path:this.curFilePath,csrf_token:csrf_token})
            .then((res)=>{
                if (res.data.code!==0){
                    this.$message.error("Load error,Cause by:\n"+res.data.message)
                    this.tableLoading=false
                    return
                }
                let data = res.data["files"]
                for (let d of data) {
                    let fileSuffix=d['fileSuffix']
                    if (!d['isDir']&&fileSuffix&&fileSuffix!==""){
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
                this.tableLoading=false
            })
        },
        createFolder(){
            if (this.folderName===""){
                this.$message.warning("文件夹名称不能为空")
                return
            }
            axios.post("/yobot/admin/setting/file/folder",{path:this.curFilePath,folderName:this.folderName,csrf_token:csrf_token})
            .then((res)=>{
                this.$message({
                    type:res.data.code===0?"success":"error",
                    message:res.data.message
                })
                if (res.data.code===0){
                    this.addVisible=false
                    this.getFileByPath({fileName:""},"this")
                }
            })
        },
        changePath(key){
            let path = ""
            this.filePaths=this.filePaths.slice(0,key+1)
            if (key>0){
                path = this.filePaths.join("\\")
            }
            this.getFileByPath({fileName:path},"click")
        },
        delDocument(d){
            this.$confirm('确认删除吗?', '提示', {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }).then(() => {
                axios.post("/yobot/admin/setting/file/delete",{path:this.curFilePath,file_name:d.fileName,csrf_token:csrf_token})
                .then((res)=>{
                    this.$message({
                        type:res.data.code===0?"success":"error",
                        message:res.data.message
                    })
                    if (res.data.code===0){
                        this.getFileByPath(d,"this")
                    }
                })
            })
        },
        submitUpload(){
            this.$refs.upload.submit();
        },
        handleRemove(file,fileList){

        },
        handlePreview(file){

        },
        handleUploadSuccess(response, file, fileList){
            if(response.code===0){
                this.$message.success("Upload success")
                this.getFileByPath({fileName: this.curFilePath},"this")
            }else{
                this.$message.error("Upload error,Cause by:\n"+response.message)
                return
            }
            fileList.length=0
        },
        handleUploadError(err, file, fileList){
            this.$message.error("Upload error")
        },
        addDialogClose(){
            this.folderName=""
            this.fileList.length=0
        },
        downloadFile(d){
            let eleLink = document.createElement('a');
              eleLink.download = d.fileName;
              eleLink.style.display = 'none';
              eleLink.href = "/yobot/admin/setting/file/view"+this.curFilePath+"/"+d.fileName;
              // 受浏览器安全策略的因素，动态创建的元素必须添加到浏览器后才能实施点击
              document.body.appendChild(eleLink);
              // 触发点击
              eleLink.click();
              // 然后移除
              document.body.removeChild(eleLink);
        },
        renameDocument(d){
            this.renameVisible=true
            this.renameFile.oldFileName=d.fileName
            this.renameFile.fileSuffix=d.fileSuffix
        },
        renameSubmit(){
            if(this.renameFile.newFileName===''){
                this.$message({message:"输入不能为空"})
                return
            }
            axios.post("/yobot/admin/setting/file/rename",
                {
                    path:this.curFilePath,
                    old_file_name:this.renameFile.oldFileName,
                    new_file_name:this.renameFile.newFileName+this.renameFile.fileSuffix,
                    csrf_token:csrf_token}
                    )
                .then((res)=>{
                    this.$message({
                        type:res.data.code===0?"success":"error",
                        message:res.data.message
                    })
                    if (res.data.code===0){
                        this.renameDialogClose()
                        this.getFileByPath({fileName:''},"this")
                    }
                })
        },
        renameDialogClose(){
            this.renameVisible=false
            this.renameFile.oldFileName=""
            this.renameFile.newFileName=""
            this.renameFile.fileSuffix=""
        },
        timeCheck(e,k,key){
            if (!e){
                let val = "*"
                if(key==="jitter"){
                    val=0
                }
                this.setting.trigger[k][key]=val
            }
        }
    },
    delimiters: ['[[', ']]'],
})