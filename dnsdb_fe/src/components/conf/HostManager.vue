<template>
  <div>
    <el-button type="info" @click="addHostGroupVisible = true">新增主机组</el-button>
    <el-button type="info" @click="fetchHostGroupList">刷新</el-button>
    <el-table
      :data="hostGroupList"
      height="500"
      style="width: 90%">
      <el-table-column label="主机组" align="center">
        <el-table-column type="expand" label="主机" width="50px">
          <template slot-scope="props">
            <el-table
              class="medium-table"
              border
              :data="props.row.hosts">
              <el-table-column prop="host_name"
                              label="主机名"
                               width="300px"
                              align="center"/>
              <el-table-column prop="host_ip"
                              label="IP"
                               width="200px"
                              align="center"/>
              <el-table-column prop="host_conf_md5"
                              label="配置md5"
                              align="center"/>
            </el-table>
          </template>
        </el-table-column>
        <el-table-column
          label="名称"
          prop="group_name"
          width="100px">
        </el-table-column>
        <el-table-column
          label="操作"
          align="center">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="danger"
              @click="handleDeleteGroup(scope.row.group_name)">删除</el-button>
            <el-button
              size="mini"
              type="primary"
              @click="handleEditGroup(scope.row.group_name, scope.row.hosts)">编辑主机</el-button>
            <el-button
              size="mini"
              type="primary"
              :disabled="!scope.row.has_conf"
              @click="getNamedConfHeader(scope.row.group_name)">编辑配置</el-button>
          </template>
        </el-table-column>
        <el-table-column
          label="reload管理"
          width="100px"
          align="center">
          <template slot-scope="scope">
            <el-tooltip class="item" effect="dark" content="Reload关闭后修改dns记录及配置将不会生效" placement="right-start">
              <el-switch
                active-text=""
                inactive-text=""
                @change="setGroupReloadStatus(scope.row)"
                v-model="scope.row.reload_status"
                active-color="#13ce66"
              />
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column
          label="配置md5"
          prop="conf_md5">
        </el-table-column>
      </el-table-column>
    </el-table>
    <el-dialog
      v-loading.body="namedConfLoading"
      title="配置编辑"
      :visible.sync="namedConfDialogVisible"
      width="90">
      <el-row :gutter="0" type="flex" >
        <el-col :span="20">
          <span class="small-title">当前主机组：{{curHostGroupName}}</span>
        </el-col>
        <el-col :span="4" style="text-align: right">
          <el-button class="button" size="small" @click="requestNamedConfHeader(curHostGroupName)">重载</el-button>
          <el-button class="button" size="small" type="danger" @click="updateNamedConfHeader">保存</el-button>
        </el-col>
      </el-row>
      <el-input
        :autosize="{ minRows: 10}"
        type="textarea"
        spellcheck="false"
        placeholder="named.conf"
        v-model="namedConf"/>
    </el-dialog>
    <el-dialog
      title="新增主机组"
      :visible.sync="addHostGroupVisible"
      width="90">
      <el-form :inline="true" :model="addGroupForm" :rules="groupRules" ref="addGroupForm" @submit.native.prevent>
        <el-form-item label="主机组名称" prop="name">
          <el-input v-model="addGroupForm.name" placeholder="xxxMaster/xxxSlave"></el-input>
        </el-form-item>
      </el-form>
      <el-table :data="addHostArray.data" border style="width: 100%" highlight-current-row>
        <el-table-column v-for="v in addHostArray.columns" :key="v.field" :prop="v.field" :label="v.title">
            <template slot-scope="scope">
                <span v-if="scope.row.isSet">
                    <el-input size="medium" v-model="addHostArray.sel[v.field]">
                    </el-input>
                </span>
                <span v-else>{{scope.row[v.field]}}</span>
            </template>
        </el-table-column>
        <el-table-column label="操作">
            <template slot-scope="scope">
                <span v-if="scope.row.isSet" class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="handleSaveHost(scope.row,scope.$index)">
                  保存
                </span>
                <span v-else class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="handleModifyHost(scope.row,scope.$index)">
                  修改
                </span>
                <span v-if="!scope.row.isSet" class="el-tag el-tag--danger el-tag--medium" style="cursor: pointer;" @click="handleDeleteHost(scope.$index)">
                    删除
                </span>
                <span v-else class="el-tag  el-tag--medium" style="cursor: pointer;" @click="handleCancelChange(scope.row,scope.$index)">
                    取消
                </span>
            </template>
        </el-table-column>
      </el-table>
      <div class="el-table-add-row" style="width: 100%;" @click="handleAddHost"><span>+ 添加</span></div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="clearHostGroupInfo">取 消</el-button>
        <el-button type="primary" @click="submitAddHostGroup">提交</el-button>
      </div>
    </el-dialog>
    <el-dialog
      :title="editGroupTitle"
      :visible.sync="editHostGroupVisible"
      width="90">
      <el-table :data="editHostArray.data" border style="width: 100%" highlight-current-row>
        <el-table-column v-for="v in editHostArray.columns" :key="v.field" :prop="v.field" :label="v.title">
            <template slot-scope="scope">
                <span v-if="scope.row.isSet">
                    <el-input size="medium" v-model="editHostArray.sel[v.field]">
                    </el-input>
                </span>
                <span v-else>{{scope.row[v.field]}}</span>
            </template>
        </el-table-column>
        <el-table-column label="操作">
            <template slot-scope="scope">
                <span v-if="scope.row.isSet" class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="submitHost(scope.row,scope.$index)">
                  提交
                </span>
                <span v-if="scope.row.isSet" class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="editHostArray.data.splice(scope.$index, 1)">
                  取消
                </span>
                <span v-if="!scope.row.isSet" class="el-tag el-tag--danger el-tag--medium" style="cursor: pointer;" @click="submitDeleteHost(scope.row.host_name, scope.$index)">
                  删除
                </span>
            </template>
        </el-table-column>
      </el-table>
      <div class="el-table-add-row" style="width: 100%;" @click="handleAddHostForModify"><span>+ 添加</span></div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="clearModifyGroupInfo">取 消</el-button>
        <el-button type="primary" @click="clearModifyGroupInfo">完成</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  var generateId = {
    _count: 1,
    get () {
      return ((+new Date()) + '_' + (this._count++))
    }
  }
  export default {
    name: 'HostManager',
    data () {
      var validateGroupName = (rule, value, callback) => {
        value = value.trim()
        if (value === '') {
          callback(new Error('请输入主机组名称'))
        } else {
          if (value.indexOf('Master') >= 0 || value.indexOf('Slave') >= 0) {
            callback()
          } else {
            callback(new Error('主机组名需要以Slave或Master结尾'))
          }
          callback()
        }
      }

      return {
        hostGroupList: [],

        addHostGroupVisible: false,
        addGroupForm: {
          name: ''
        },
        groupRules: {
          name: [
            { validator: validateGroupName, trigger: 'blur' }
          ]
        },
        addHostArray: {
          sel: null, // 选中行
          columns: [
            { field: 'name', title: '主机名' },
            { field: 'ip', title: '主机ip' }
          ],
          data: []
        },

        editHostGroupVisible: false,
        editGroupTitle: '',
        editHostArray: {
          groupName: '',
          sel: null, // 选中行
          columns: [
            { field: 'host_name', title: '主机名' },
            { field: 'host_ip', title: '主机ip' }
          ],
          data: []
        },

        curHostGroupName: '',
        namedConf: '',
        namedConfDialogVisible: false,
        namedConfLoading: false,
        hasNamedConf: false
      }
    },

    mounted () {
      this.fetchHostGroupList()
    },

    methods: {
      fetchHostGroupList () {
        this.$http.get('/web/config/list/host_group')
          .then((res) => {
            this.hostGroupList = res.data.data
          }).catch((err) => {
            console.log(err)
          })
      },

      handleAddHost () {
        for (let index in this.addHostArray.data) {
          let row = this.addHostArray.data[index]
          if (row.isSet) {
            if (!this.handleSaveHost(row, index)) return
          }
        }
        let j = { name: '', ip: '', isSet: true }
        this.addHostArray.data.push(j)
        this.addHostArray.sel = JSON.parse(JSON.stringify(j))
      },

      handleSaveHost (row, index) {
        let data = JSON.parse(JSON.stringify(this.addHostArray.sel))
        for (let k in data) {
          let value = data[k]
          if (k === 'name' || k === 'ip') {
            value = value.trim()
            if (value === '') {
              this.$message.warning('字段不能为空')
              return false
            }
          }
          row[k] = value
        }
        //  然后这边重新读取表格数据
        this.readHostArray()
        row.isSet = false
        return true
      },

      handleCancelChange (row, index) {
        // 如果是新加的行，删除数据
        if (!this.addHostArray.sel.id) {
          this.addHostArray.data.splice(index, 1)
          return
        }
        row.isSet = !row.isSet
      },

      handleDeleteHost (index) {
        this.addHostArray.data.splice(index, 1)
      },

      handleModifyHost (row, index) {
        for (let i in this.addHostArray.data) {
          let data = this.addHostArray.data[i]
          if (data.isSet && data.id !== row.id) {
            if (!this.handleSaveHost(data, i)) {
              return false
            }
          }
        }
        this.addHostArray.sel = JSON.parse(JSON.stringify(row))
        row.isSet = true
      },

      readHostArray () {
        this.addHostArray.data.map(i => {
          i.id = generateId.get()
          i.isSet = false
          return i
        })
      },

      clearHostGroupInfo () {
        this.addHostGroupVisible = false
        this.addHostArray.sel = {}
        this.addHostArray.data = []
        this.addGroupForm.name = ''
      },

      clearModifyGroupInfo () {
        this.fetchHostGroupList()
        this.editHostGroupVisible = false
        this.editHostArray.sel = {}
        this.editHostArray.data = []
        this.editHostArray.groupName = ''
      },

      submitAddHostGroup () {
        for (let i in this.addHostArray.data) {
          let data = this.addHostArray.data[i]
          if (data.isSet) {
            if (!this.handleSaveHost(data, i)) {
              // this.$message.warning('请先保存当前编辑项')
              return false
            }
          }
        }
        this.$refs['addGroupForm'].validate((valid) => {
          if (valid) {
            let params = {group_name: this.addGroupForm.name, hosts: []}
            let hosts = []
            let data = this.addHostArray.data
            for (let i in data) {
              hosts.push({host_name: data[i].name, host_ip: data[i].ip})
            }
            params['hosts'] = hosts
            util.post(this, {
              url: '/web/config/add/host_group',
              data: params,
              succ: (data) => {
                this.$notify.success({
                  title: '成功',
                  message: '新加主机组成功',
                  duration: 1500
                })
                this.fetchHostGroupList()
                this.clearHostGroupInfo()
              }
            })
          } else {
            return false
          }
        })
      },

      handleDeleteGroup (groupName) {
        this.$confirm('确认删除主机组 ' + groupName, '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
          .then(() => {
            util.post(this, {
              url: '/web/config/delete/host_group',
              data: {group_name: groupName},
              succ: (data) => {
                util.notify(this, '成功', '删除主机组成功')
                this.fetchHostGroupList()
              }
            })
          })
          .catch(() => {})
      },

      handleEditGroup (groupName, hosts) {
        this.editGroupTitle = '编辑主机组: ' + groupName
        this.editHostGroupVisible = true
        this.editHostArray.data = hosts
        this.editHostArray.groupName = groupName
      },

      handleAddHostForModify () {
        for (let index in this.editHostArray.data) {
          let row = this.editHostArray.data[index]
          if (row.isSet) {
            this.$message.warning('请先提交当前编辑项')
            return false
          }
        }
        let j = { host_name: '', host_ip: '', isSet: true }
        this.editHostArray.data.push(j)
        this.editHostArray.sel = JSON.parse(JSON.stringify(j))
      },

      submitHost (row, index) {
        let data = JSON.parse(JSON.stringify(this.editHostArray.sel))
        for (let k in data) {
          let value = data[k]
          if (k === 'host_name' || k === 'host_ip') {
            value = value.trim()
            if (value === '') {
              this.$message.warning('字段不能为空')
              return false
            }
          }
          row[k] = value
        }
        //  然后这边重新读取表格数据
        util.post(this, {
          url: 'web/config/add/host',
          data: {group_name: this.editHostArray.groupName, host_ip: row.host_ip, host_name: row.host_name},
          succ: (data) => {
            this.$notify.success({
              title: '成功',
              message: '新加主机成功',
              duration: 1500
            })
            row.isSet = false
            return true
          }
        })
      },

      submitDeleteHost (hostName, index) {
        for (let index in this.editHostArray.data) {
          let row = this.editHostArray.data[index]
          if (row.isSet) {
            this.$message.warning('请先提交当前编辑项')
            return false
          }
        }
        this.$confirm('确认删除主机 ' + hostName, '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
          .then(() => {
            util.post(this, {
              url: 'web/config/delete/host',
              data: {host_name: hostName, group_name: this.editHostArray.groupName},
              succ: (data) => {
                this.$notify.success({
                  title: '成功',
                  message: '删除主机成功',
                  duration: 1500
                })
                this.editHostArray.data.splice(index, 1)
              }
            })
          })
          .catch(() => {})
      },

      getNamedConfHeader (groupName) {
        this.curHostGroupName = groupName
        this.requestNamedConfHeader(groupName)
        this.namedConfDialogVisible = true
      },

      requestNamedConfHeader (groupName) {
        util.get(this, {
          url: '/web/config/get/named_conf_header',
          data: {group_name: groupName},
          succ: (data) => {
            console.log(data)
            this.namedConf = data.data
          }
        })
      },

      updateNamedConfHeader () {
        this.$confirm('是否保存 ' + this.curHostGroupName + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.namedConfLoading = true
          util.post(this, {
            url: '/web/config/update/named_conf_header',
            data: {name: this.curHostGroupName, conf_content: this.namedConf},
            succStr: '保存成功'
          })
          this.namedConfLoading = false
          this.namedConfDialogVisible = false
          this.fetchHostGroupList()
        }).catch(() => { })
      },

      setGroupReloadStatus (row) {
        let status = row.reload_status
        let msg = '是否'
        if (status) {
          msg += '打开 reload?'
        } else {
          msg += '关闭 reload?'
        }
        this.$confirm(msg, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          status = status ? 1 : 0
          util.post(this, {
            url: '/web/config/update/group_reload_status',
            data: {reload_status: status, group_name: row.group_name},
            succStr: '设置Reload状态成功',
            fail: (data) => {
              row.reload_status = !status
              this.$confirm(data.message + '，请检查后重试', '失败', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
              })
                .then(() => {})
                .catch(() => {})
            }
          })
        }).catch(() => {
          row.reload_status = !status
          this.$message({
            type: 'info',
            message: '已取消切换'
          })
        })
      }
    }
  }
</script>

<style scoped>

  .el-table-add-row {
    margin-top: 10px;
    width: 100%;
    height: 34px;
    border: 1px dashed #c1c1cd;
    border-radius: 3px;
    cursor: pointer;
    justify-content: center;
    display: flex;
    line-height: 34px;
  }

  .list-item {
    width:200px;
    line-height: 40px;
    cursor:pointer;
    height: 40px;
    display: inline-block;
    border-bottom: 1px solid lightgray;
  }

  .medium-button-div {
    display: inline-block;
    line-height: 30px;
    margin-bottom: 3px;
  }
</style>
