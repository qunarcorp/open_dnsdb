<template>
  <div class="tab-panel">
    <div>
      <el-row>
        <el-col :span="12"><div class="grid-content">
           <el-input 
              class="large-input"
              size="large" 
              placeholder="请输入ip" 
              v-model="searchIP"
              @keyup.enter.native="searchAclByIP"
              @change="searchAclByIP"/>
          <el-button size="large" @click="searchAclByIP">搜索</el-button>
        </div></el-col>
        <el-col :span="12"><div class="grid-content">
          <el-button size="large" style="display: inline-block;margin-left: 2px" @click="addSubnetVisible = true">新增网段</el-button>
        </div></el-col>
      </el-row>
      <div>
        <el-table
          class="medium-table"
          v-loading="subnetLoading"
          height="500px"
          border
          :data="aclRecordList">
          <el-table-column 
            prop="subnet"
            label="网段"
            align="center"/>
          <el-table-column
            label="所属运营商"
            align="center">
            <template slot-scope="scope">
              <span class="demonstration"> {{ aclIspDict[scope.row.origin_acl] }} </span>
            </template>        
          </el-table-column>
          <el-table-column
            label="当前运营商"
            align="center">
            <template slot-scope="scope">
              <span class="demonstration"> {{ aclIspDict[scope.row.now_acl] }} </span>
            </template>  
          </el-table-column>
          <el-table-column
            label="操作"
            align="center">
            <template slot-scope="scope">
              <el-button 
                size="small"
                v-if="!scope.row.batch_locked"
                @click="showMigrateDialog(scope.row.id, scope.row.now_acl)">
                迁移
              </el-button>
              <el-button size="small" v-if="scope.row.now_acl !== scope.row.origin_acl"
                        @click="subnetIspRecover(scope.row.id, scope.row.origin_acl, scope.row.subnet)">
                恢复
              </el-button>
              <el-button size="small" @click="deleteSubnet(scope.row.id)">
                删除
              </el-button>
            </template>        
          </el-table-column>
        </el-table>
      </div>
    </div>
    <el-dialog
      title="subnet迁移"
      :visible.sync="subnetMigrateVisible">
      <label for="select">选择运营商</label>
      <el-select v-model="migrate2acl" clearable placeholder="目标运营商" @change="handleChoiceIsp">
        <el-option
          v-for="item in IspOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
          :disabled="migrateSubnetFrom === item.value">
          <span style="float: left">{{ item.label }}</span>
        </el-option>
      </el-select>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="migrate2acl=''; subnetMigrateVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSubnetMigrate">迁移</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="acl网段新增"
      :visible.sync="addSubnetVisible">
      <el-form :inline="true" class="demo-form-inline">
        <el-form-item label="运营商">
          <el-select v-model="addSubnetAcl" clearable>
            <el-option
              v-for="item in IspOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
              <span style="float: left">{{ item.label }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="网段">
          <el-input
            v-model="addSubnet"
            @keyup.enter.native="checkSubnet"/>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="addSubnetVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddSubnet">新增</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'AclManager',
    data () {
      return {
        searchIP: '',
        subnetLoading: false,
        aclRecordList: [],
        subnetMigrateVisible: false,
        acMigrateSubnetId: -1,
        migrateSubnetFrom: '',
        migrate2acl: '',

        IspOptions: [],
        aclIspDict: {},

        addSubnetVisible: false,
        addSubnetAcl: '',
        addSubnet: ''
      }
    },

    mounted () {
      this.fetchMigrateSubnet()
      this.fetchViewIspInfo()
    },

    methods: {
      fetchViewIspInfo () {
        util.get(this, {
          url: '/web/view/list/acl_isp_info',
          succ: (data) => {
            let obj = data.data
            console.log(obj)
            this.aclIspDict = obj
            this.IspOptions = util.objToOptions(obj)
          }
        })
      },

      searchAclByIP () {
        this.searchIP = this.searchIP.trim()
        if (this.searchIP === '') {
          this.fetchMigrateSubnet()
          // this.$message.warning('条件不能为空')
          return false
        }
        this.subnetLoading = true
        this.aclRecordList = []
        util.get(this, {
          url: '/web/view/list/acl_subnet_by_ip',
          data: {ip: this.searchIP},
          succ: (data) => {
            this.aclRecordList = data.data
            this.subnetLoading = false
          }
        })
        this.subnetLoading = false
      },

      showMigrateDialog (aclSubnetId, nowAcl) {
        this.subnetMigrateVisible = true
        this.acMigrateSubnetId = aclSubnetId
        this.migrateSubnetFrom = nowAcl
      },

      postMigrateSubnet () {
        util.post(this, {
          url: '/web/view/migrate_subnet_acl',
          data: {acl_subnet_id: this.acMigrateSubnetId, to_acl: this.migrate2acl},
          succ: (data) => {
            util.notify(this, '成功', '网段迁移成功')
            this.searchAclByIP()
            this.subnetMigrateVisible = false
          }
        })
      },

      handleSubnetMigrate () {
        if (!this.migrate2acl) {
          this.$message.warning('请选择目标运营商')
          return false
        } else {
          this.postMigrateSubnet()
        }
      },

      fetchMigrateSubnet () {
        this.subnetLoading = true
        util.get(this, {
          url: '/web/view/list/migrate_subnet',
          succ: (data) => {
            this.aclRecordList = data.data
            this.subnetLoading = false
          }
        })
        this.subnetLoading = false
      },

      subnetIspRecover (subnetId, subnetOriginAcl, subnet) {
        this.$confirm('是否恢复运营商', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.migrate2acl = subnetOriginAcl
          this.acMigrateSubnetId = subnetId
          this.postMigrateSubnet()
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '已取消恢复',
            duration: 1500
          })
        })
      },

      handleChoiceIsp () {
        console.log(this.migrate2acl)
      },

      handleAddSubnet () {
        if (!this.checkSubnet()) {
          return false
        }
        this.$confirm('是否添加网段' + this.addSubnetAcl, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/view/add/acl_subnet',
            data: {acl: this.addSubnetAcl, subnet: this.addSubnet},
            succ: (data) => {
              this.searchIP = this.addSubnet.split('/')[0]
              this.addSubnetVisible = false
              this.searchAclByIP()
            }
          })
        }).catch(() => {
          this.$message.info('已取消新增')
        })
      },

      deleteSubnet (subnetId) {
        util.post(this, {
          url: '/web/view/delete/acl_subnet',
          data: {subnet_id: subnetId},
          succ: (data) => {
            util.notify(this, '成功', '删除网段成功')
            this.searchAclByIP()
          }
        })
      },

      checkSubnet () {
        let value = this.addSubnet
        let sub = value.split('/')[0]
        if (value === '') {
          this.$message.warning('请输入网段')
          return false
        } else if (value.indexOf('/') < 0) {
          this.$message.warning('请输入cidr格式网段: 192.168.0.0/24')
          return false
        } else if (!util.isValidIP(sub)) {
          this.$message.warning('网段格式错误')
          return false
        }
        return true
      }
    }
  }
</script>

<style scoped>
  .table-item {
    line-height: 30px;
    height: 30px;
    margin-left: 3px;
    margin-bottom: 2px;
    margin-top: 2px;
    padding:2px;
    background:aliceblue;
    overflow: visible;
    display: inline-table;
  }

  .condition-div {
    padding-left: 10px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

</style>
