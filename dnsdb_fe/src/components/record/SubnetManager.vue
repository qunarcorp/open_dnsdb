<template>
  <div class="tab-panel">
    <div class="tab-panel">
      <el-row>
        <el-col :span="16"><div class="grid-content">
          <el-select v-model="searchType" clearable size='large' placeholder="请选择">
            <el-option
            v-for="item in searchOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value">
            </el-option>
          </el-select>
          <el-input class="large-input" v-model="searchCondition" size="large"
                @keyup.enter.native="searchGeneral"/>
          <el-button size="large" type="primary"  @click="searchGeneral">搜索</el-button>
        </div></el-col>
        <el-col :span="8"><div class="grid-content">
          <el-button size="large" style="display: inline-block;margin-left: 2px" @click="addSubnetVisible = true">新建子网</el-button>
        </div></el-col>
      </el-row>
    </div>
    <hr />
    <el-table
      border
      class="medium-table"
      v-loading="loadingSubnet"
      height="600"
      :data="subnetsList">
      <el-table-column prop="region_name"
                        label="区域"
                        align="center"/>
      <el-table-column prop="subnet"
                        label="子网"
                        align="center">
      </el-table-column>
      <el-table-column prop="intranet"
                        label="类型"
                        align="center">
        <template slot-scope="scope">
          <span v-if="scope.row.intranet">私网</span>
          <span v-else>公网</span>
        </template>
      </el-table-column>
      <el-table-column prop="create_user"
                        label="创建用户"
                        align="center"/>
      <el-table-column prop="comment"
                        label="备注"
                        align="center"/>
      <el-table-column prop="operation"
                        label="操作"
                        width="300px"
                        align="center">
        <template slot-scope="scope">
          <el-button type="info" size="small" :plain="true" @click="fetchSubnetIp(scope.row.region_name)">IP详情</el-button>
          <el-button type="warning" size="small" :plain="true" @click="openRenameDialog(scope.row.region_name)">重命名</el-button>
          <el-button type="danger" size="small" :plain="true" @click="deleteSubnet(scope.row.region_name,scope.row.subnet)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog
      title="重命名子网"
      :visible.sync="renameSubnetVisible"
      width="40%">
      <el-form ref="renameForm" label-position="left" :model="renameForm" label-width="120px" :rules="subnetRules">
        <el-form-item label="原子网名称">
          <el-input v-model="renameForm.oldRegion" :disabled="true"></el-input>
        </el-form-item>
        <el-form-item label="修改后子网名称" prop="newRegion">
          <el-input v-model="renameForm.newRegion"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="renameSubnetVisible = false">取 消</el-button>
        <el-button type="primary" @click="renameSubnet">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="新增子网"
      :visible.sync="addSubnetVisible"
      width="40%">
      <el-form ref="subnetForm" label-position="left" :model="subnetForm" label-width="80px" :rules="subnetRules">
        <el-form-item label="名称" prop="region">
          <el-input v-model="subnetForm.region"></el-input>
        </el-form-item>
        <el-form-item label="子网" prop="subnet">
          <el-input v-model="subnetForm.subnet"></el-input>
        </el-form-item>
        <el-form-item label="机房" prop="colo">
          <el-select v-model="subnetForm.colo" clearable size='large'>
            <el-option
              v-for="item in coloOpions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="subnetForm.comment"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="clearSubnetForm">取 消</el-button>
        <el-button type="primary" @click="addSubnet">提 交</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="子网详情"
      :visible.sync="SubnetDetailVisible"
      width="50%">
      <el-table
        class="medium-table"
        height="500"
        :data="ipList">
        <el-table-column prop="ip"
                         label="IP"
                         align="center"/>
        <el-table-column prop="ipStatus"
                         label="IP状态"
                         align="center">
          <template slot-scope="scope">
            <div v-if="scope.row.domain" style="color: red">
              使用
            </div>
            <div v-else style="color: green">
              可用
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="domain"
                         label="域名"
                         align="center"/>
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="SubnetDetailVisible = false">关 闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'SubnetManager',
    data () {
      var validateSubnet = (rule, value, callback) => {
        value = value.trim()
        let sub = value.split('/')[0]
        if (value === '') {
          callback(new Error('请输入网段'))
        } else if (value.indexOf('/') < 0) {
          callback(new Error('请输入cidr格式网段: 192.168.0.0/24'))
        } else if (!util.isValidIP(sub)) {
          callback(new Error('网段格式错误'))
        } else {
          callback()
        }
      }

      var validateRegion = (rule, value, callback) => {
        console.log(value)
        value = value.trim()
        var reg = /^[a-zA-Z0-9_]+$/
        if (value === '') {
          callback(new Error('请输入网段名称'))
        } else if (!reg.test(value)) {
          callback(new Error('只能包含大小写字母、数字、下划线'))
        } else if (value.length <= 0 || value.length > 64) {
          callback(new Error('网段名称长度在[1-64]之间'))
        } else {
          callback()
        }
      }

      return {
        subnetsList: [],
        loadingSubnet: false,
        colos: [],
        coloOpions: [],
        searchOptions: [{
          label: 'IP',
          value: 'IP'
        }, {
          label: 'region',
          value: 'region'
        }],
        searchType: 'IP',
        searchCondition: '',

        renameSubnetVisible: false,
        renameForm: {
          oldRegion: '',
          newRegion: ''
        },

        addSubnetVisible: false,
        subnetForm: {
          region: '',
          subnet: '',
          colo: '',
          comment: ''
        },
        subnetRules: {
          region: [
            { required: true, message: '请输入网段名称', trigger: 'blur' },
            { validator: validateRegion, trigger: 'blur' }
          ],
          newRegion: [
            { required: true, message: '请输入网段名称', trigger: 'blur' },
            { validator: validateRegion, trigger: 'blur' }
          ],
          subnet: [
            { required: true, message: '198.18.4.0/22', trigger: 'blur' },
            { validator: validateSubnet, trigger: 'blur' }
          ],
          colo: [
            { required: true, message: '请选择机房', trigger: 'blur' }
          ]
        },

        SubnetDetailVisible: false,
        ipList: []
      }
    },

    mounted () {
      this.fetchColos()
      this.fetchAllSubnet()
    },

    methods: {
      fetchColos () {
        util.get(this, {
          'url': '/web/subnet/get/subnet_colos',
          succ: (data) => {
            this.colos = data.data
            this.coloOpions = util.arrayToOptions(this.colos)
          }
        })
      },

      fetchAllSubnet () {
        this.loadingSubnet = true
        util.get(this, {
          url: '/web/subnet/list/region',
          succ: (data) => {
            this.subnetsList = data.data
          }
        })
        this.loadingSubnet = false
      },

      fetchSubnetIp (region) {
        util.get(this, {
          url: '/web/subnet/get/subnet_ip',
          data: {region: region},
          succ: (data) => {
            this.ipList = data.data
            this.SubnetDetailVisible = true
          }
        })
      },

      searchGeneral () {
        // 默认按ip搜索
        let url = '/web/subnet/get/region_by_ip'
        let param = {ip: this.searchCondition}
        if (this.searchCondition === '') {
          this.fetchAllSubnet()
          return
        } else if (this.searchType === 'region') {
          url = '/web/subnet/get/region_by_name'
          param = {region: this.searchCondition}
        }
        util.get(this, {
          url: url,
          data: param,
          succ: (data) => {
            this.subnetsList = data.data
          }
        })
      },

      clearSubnetForm () {
        this.addSubnetVisible = false
        this.subnetForm = {
          region: '',
          subnet: '',
          colo: '',
          comment: ''
        }
      },

      addSubnet () {
        this.$refs['subnetForm'].validate((valid) => {
          if (valid) {
            this.$confirm('是否新建子网' + this.subnetForm.region + '?', '提示', {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }).then(() => {
              util.post(this, {
                url: '/web/subnet/add/subnet',
                data: this.subnetForm,
                succ: (data) => {
                  util.notify(this, '成功', '新增子网成功')
                  this.fetchAllSubnet()
                  this.clearSubnetForm()
                }
              })
            }).catch(() => {
              this.$message({
                type: 'info',
                message: '已取消新建'
              })
            })
          } else {
            return false
          }
        })
      },

      deleteSubnet (region, subnet) {
        this.$confirm('是否删除' + region + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/subnet/delete',
            data: {region: region, subnet: subnet},
            succ: (data) => {
              util.notify(this, '成功', '删除子网成功')
              this.searchGeneral()
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除'
          })
        })
      },

      openRenameDialog (oldRegion) {
        this.renameSubnetVisible = true
        this.renameForm.oldRegion = oldRegion
        this.renameForm.newRegion = ''
      },

      renameSubnet () {
        this.$refs['renameForm'].validate((valid) => {
          if (valid) {
            this.$confirm('是否重命名子网' + this.renameForm.oldRegion + '?', '提示', {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }).then(() => {
              util.post(this, {
                url: '/web/subnet/rename_subnet',
                data: {old_region: this.renameForm.oldRegion, new_region: this.renameForm.newRegion},
                succ: (data) => {
                  util.notify(this, '成功', '重命名子网成功')
                  this.renameSubnetVisible = false
                  this.searchGeneral()
                }
              })
            }).catch(() => {
              this.$message({
                type: 'info',
                message: '已取消重命名'
              })
            })
          } else {
            return false
          }
        })
      }
    }
  }
</script>

<style scoped>

</style>
