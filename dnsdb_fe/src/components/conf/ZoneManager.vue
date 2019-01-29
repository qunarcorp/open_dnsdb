<template>
  <div>
    <el-button type="info" @click="openAddConfDialog">新增Zone</el-button>
    <el-table
      v-loading.fullscreen.lock="zoneConfLoading"
      class="small-table"
      border
      :data="zoneConfList">
      <el-table-column prop="zone_name"
                       label="Zone"
                       align="center"/>
      <el-table-column prop="zone_group"
                       label="生效主机组"
                       align="center">
        <template slot-scope="scope">
                <span v-for="item in scope.row.zone_group">
                  {{ item }}
                </span>
        </template>
      </el-table-column>
      <el-table-column prop="operation"
                       label="操作"
                       align="center">
        <template slot-scope="scope">
          <el-button size="small" @click="openEditConfDialog(scope.row.zone_name)">编辑</el-button>
          <el-button type="danger" size="small" @click="deleteZoneConf(scope.row.zone_name)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div>
      <el-dialog
        v-if="editZoneDialogVisible"
        :title="editZoneName"
        :visible.sync="editZoneDialogVisible">
        <el-row :gutter="0" type="flex" >
          <el-col :span="4">
            <span class="small-title">主机组：</span>
            <div v-for="conf in editZoneConf" >
              <el-checkbox :checked="conf.use" @change="selectGroupConf(conf)"/>
              <span @click="getEditGroupConf(conf.group)" class="small-list-item">{{ conf.group }}</span>
            </div>
          </el-col>
          <el-col :span="20">
            <el-row :gutter="0" type="flex"  style="margin-bottom: 5px">
              <el-col :span="16">
                <label class="small-title">编辑主机组：{{ editGroupConf.group}}</label>
                <label class="zone-type-label">Zone类型</label>
                <el-select class="zone-type-select" size="small" v-model="editZoneType" placeholder="Zone类型">
                  <el-option
                    v-for="item in options"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
                </el-select>
              </el-col>
              <el-col :span="8" style="text-align: right">
                <el-button class="button" size="small" @click="editGetTemplate(editZoneName,editGroupConf.group)">填入模板</el-button>
              </el-col>
            </el-row>
            <el-input
              v-if="editGroupConf"
              :autosize="{ minRows: 10}"
              type="textarea"
              spellcheck="false"
              placeholder="zone conf"
              v-model="editGroupConf.conf">
            </el-input>
          </el-col>
        </el-row>
        <span slot="footer" class="dialog-footer">
          <el-button @click="openEditConfDialog(editZoneName)">重 载</el-button>
          <el-button type="warning" @click="checkConf(editZoneConf)">检 查</el-button>
          <el-button type="primary" @click="submitEditConf">保 存</el-button>
        </span>
      </el-dialog>
      <el-dialog
        v-if="addZoneDialogVisible"
        title="新增Zone"
        :visible.sync="addZoneDialogVisible">
        <el-input size="small" v-model="addZoneName" placeholder="新增Zone名" style="width: 300px" :disabled="true"></el-input>
        <el-tooltip class="item" effect="dark" content="Zone为forward类型无需勾选" placement="right-start">
          <el-checkbox style="margin-left: 20px" v-model="addZoneHeader" label="新增头文件"/>
        </el-tooltip>
        <label class="zone-type-label">Zone类型</label>
        <el-select class="zone-type-select" size="small" v-model="addZoneType" placeholder="Zone">
          <el-option
            v-for="item in options"
            :key="item.value"
            :label="item.label"
            :value="item.value">
          </el-option>
        </el-select>
        <el-row :gutter="0" type="flex" style="margin-top: 10px">
          <el-col :span="4">
            <span class="small-title">主机组：</span>
            <div v-for="conf in addZoneConf" >
              <el-checkbox :checked="conf.use" @change="selectGroupConf(conf)"/>
              <span class="small-list-item" @click="getAddGroupConf(conf.group)" >{{ conf.group }}</span>
            </div>
          </el-col>
          <el-col :span="20">
            <span class="small-title">编辑主机组：{{ addGroupConf.group}}</span>
            <el-input
              v-if="addGroupConf"
              :autosize="{ minRows: 10}"
              type="textarea"
              spellcheck="false"
              placeholder="zone conf"
              v-model="addGroupConf.conf">
            </el-input>
          </el-col>
        </el-row>
        <span slot="footer" class="dialog-footer">
          <el-button type="warning" @click="checkConf(addZoneConf)">检 查</el-button>
          <el-button type="primary" @click="submitAddConf">保 存</el-button>
        </span>
      </el-dialog>
    </div>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'ZoneManager',
    data () {
      return {
        options: [{
          value: 0,
          label: '反解'
        }, {
        //   value: 1,
        //   label: '机房'
        // }, {
          value: 2,
          label: '普通'
        }],

        hostGroupList: [],
        zoneConfList: [],
        zoneConfLoading: false,
        editZoneDialogVisible: false,
        editZoneName: '',
        editZoneConf: [],
        editZoneType: 2,
        editGroupConf: '',

        addZoneDialogVisible: false,
        addZoneConf: [],
        addZoneName: '',
        addGroupConf: '',
        addZoneType: 2,
        addZoneHeader: true
      }
    },

    mounted () {
      this.fetchHostGroupList()
      this.fetchZoneConfList()
    },

    methods: {
      fetchHostGroupList () {
        util.get(this, {
          url: '/web/config/get/has_named_group',
          succ: (data) => {
            this.hostGroupList = data.data
          }
        })
      },

      fetchZoneConfList () {
        util.get(this, {
          url: '/web/config/list/named_zone',
          succ: (data) => {
            this.zoneConfList = data.data
          }
        })
      },

      openEditConfDialog (zoneName) {
        util.get(this, {
          url: '/web/config/get/named_zone',
          data: {zone_name: zoneName},
          succ: (data) => {
            this.editZoneDialogVisible = true
            this.editZoneName = zoneName
            this.editZoneType = data.data.zone_type
            this.editZoneConf = data.data.zone_conf
            this.wrapEditConf(this.editZoneName, this.editZoneConf)
            this.editGroupConf = this.editZoneConf[0]
          }
        })
      },

      openAddConfDialog () {
        this.$prompt('请输入Zone名', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          inputPlaceholder: 'Zone名',
          inputErrorMessage: 'Zone名格式不正确'
        }).then(({ value }) => {
          this.addZoneType = 2
          if (value.indexOf('.IN-ADDR.ARPA') >= 0) {
            this.addZoneType = 0
          }
          this.addZoneName = value
          this.addZoneConf = []
          this.buildZoneConf(this.addZoneName, this.addZoneConf)
          this.addGroupConf = this.addZoneConf[0]
          this.addZoneDialogVisible = true
          this.addZoneHeader = true
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '取消新增'
          })
        })
      },

      getEditGroupConf (group) {
        for (let i = 0; i < this.editZoneConf.length; i++) {
          if (this.editZoneConf[i].group === group) {
            this.editGroupConf = this.editZoneConf[i]
          }
        }
      },

      getAddGroupConf (group) {
        for (let i = 0; i < this.addZoneConf.length; i++) {
          if (this.addZoneConf[i].group === group) {
            this.addGroupConf = this.addZoneConf[i]
          }
        }
      },

      // 添加对应的模板文件
      editGetTemplate (zoneName, group) {
        if (group.indexOf('Master') >= 0) {
          this.editGroupConf.conf = this.getTemplateConf(zoneName, 'master')
        } else {
          this.editGroupConf.conf = this.getTemplateConf(zoneName, 'slave')
        }
      },

      buildZoneConf (zoneName, addZoneConf) {
        if (addZoneConf.length !== 0) {
          return
        }
        for (let i in this.hostGroupList) {
          let group = this.hostGroupList[i].group_name
          if (group.indexOf('Master') >= 0) {
            addZoneConf.push({group: group, conf: this.getTemplateConf(zoneName, 'master')})
          } else {
            addZoneConf.push({group: group, conf: this.getTemplateConf(zoneName, 'slave')})
          }
          addZoneConf[addZoneConf.length - 1].use = false
        }
      },

      // 添加缺少的主机组配置，并得到生效的主机组
      wrapEditConf (zoneName, editZoneConf) {
        for (let i in this.hostGroupList) {
          let hasConf = false
          let group = this.hostGroupList[i].group_name
          for (let j in editZoneConf) {
            if (editZoneConf[j].group === group) {
              hasConf = true
              editZoneConf[j].use = true
            }
          }
          if (!hasConf) {
            if (group.indexOf('Master') >= 0) {
              editZoneConf.push({group: group, conf: this.getTemplateConf(zoneName, 'master')})
            } else {
              editZoneConf.push({group: group, conf: this.getTemplateConf(zoneName, 'slave')})
            }
            editZoneConf[editZoneConf.length - 1].use = false
          }
        }
      },

      unWrapEditConf (editZoneConf) {
        let commitConf = {}
        for (let i in editZoneConf) {
          if (editZoneConf[i].use) {
            commitConf[editZoneConf[i].group] = editZoneConf[i].conf
          }
        }
        if (JSON.stringify(commitConf) === '{}') {
          util.notify(this, '错误', '至少有一组生效主机', 'error')
          return false
        }
        return commitConf
      },

      getFileNameFromZoneName (zoneName) {
        if (zoneName.indexOf('.IN-ADDR.ARPA') > 0) {
          let filename = zoneName.replace('.IN-ADDR.ARPA', '')
          filename = filename.split('.').reverse().join('.') + '.zone'
          return filename
        } else {
          return zoneName
        }
      },

      getTemplateConf (zoneName, type) {
        let filename = this.getFileNameFromZoneName(zoneName)
        let conf = 'empty'
        if (type === 'master') {
          conf = `zone "${zoneName}" {\n\ttype master;\n\tfile "${filename}";\n};`
        } else {
          conf = `zone "${zoneName}" {\n\ttype slave;\n\tfile "slave/${filename}";\n\tmasters {\n\t\t ip_of_master;\n\t};\n};`
        }
        return conf
      },

      selectGroupConf (conf) {
        conf.use = !conf.use
      },

      checkConf (confArray) {
        let commitConf = this.unWrapEditConf(confArray)
        if (!commitConf) {
          return false
        }
        util.post(this, {
          url: 'web/config/check_named_zone',
          data: {zone: this.addZoneName, conf: commitConf},
          succStr: '语法检查通过'
        })
      },

      submitEditConf () {
        let commitConf = this.unWrapEditConf(this.editZoneConf)
        if (!commitConf) {
          return false
        }
        this.$confirm('是否修改 ' + this.editZoneName + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/config/update/named_zone',
            data: {zone: this.editZoneName, zone_type: this.editZoneType, conf: commitConf},
            succ: (data) => {
              util.notify(this, '成功', '修改成功')
              this.editZoneDialogVisible = false
              this.zoneConfLoading = true
              this.fetchZoneConfList()
              this.zoneConfLoading = false
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消修改'
          })
        })
      },

      submitAddConf () {
        let commitConf = this.unWrapEditConf(this.addZoneConf)
        if (!commitConf) {
          return false
        }
        this.$confirm('是否新增 ' + this.addZoneName + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/config/add/named_zone',
            data: {zone: this.addZoneName, zone_type: this.addZoneType, conf: commitConf, add_header: this.addZoneHeader},
            succ: (data) => {
              util.notify(this, '成功', '修改成功')
              this.addZoneDialogVisible = false
              this.zoneConfLoading = true
              this.fetchZoneConfList()
              this.zoneConfLoading = false
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消新增'
          })
        })
      },

      deleteZoneConf (zoneName) {
        this.$confirm('是否删除 ' + zoneName + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/config/delete/named_zone',
            data: {zone: zoneName},
            succ: (data) => {
              util.notify(this, '成功', '删除成功')
              this.zoneConfLoading = true
              this.fetchZoneConfList()
              this.zoneConfLoading = false
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除'
          })
        })
      }
    }
  }
</script>

<style scoped>
  .zone-type-label {
    margin-left: 20px;
  }
  .zone-type-select {
    margin-left: 5px;
    width: 100px;
  }
</style>
