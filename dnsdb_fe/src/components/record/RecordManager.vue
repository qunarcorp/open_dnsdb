<template>
  <div class="tab-panel">
    <div>
      <el-row>
        <el-col :span="16"><div class="grid-content">
          <el-select v-model="searchType" clearable size='large' placeholder="请选择" @change="searchCondition=''">
            <el-option
              v-for="item in typeOptions"
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
          <el-button size="large" style="display: inline-block;margin-left: 2px" @click="addRecordVisible = true">新增域名</el-button>
        </div></el-col>
      </el-row>
    </div>
    <hr />
    <div class="tab-panel">
      <el-table
        :data="recordList">
        <el-table-column prop="domain_name"
                         label="域名"
                         width="300px"
                         align="center"/>
        <el-table-column prop="record_type"
                         label="类型"
                         width="100px"
                         align="center"/>
        <el-table-column prop="record"
                         label="记录"
                         width="200px"
                         align="center"/>
        <el-table-column prop="ttl"
                         label="TTL"
                         width="100px"
                         align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.ttl===0">默认</span>
            <span v-else>{{scope.row.ttl}}</span>
          </template>
        </el-table-column>
        <el-table-column prop="zone_name"
                         label="zone"
                         width="140px"
                         align="center"/>
        <el-table-column prop="update_user"
                         label="创建用户"
                         align="center"/>
        <el-table-column prop="created_time"
                         label="创建时间"
                         align="center">
          <template slot-scope="scope">
            {{scope.row.created_time.substring(0,19)}}
          </template>
        </el-table-column>>
        <el-table-column prop="operaion"
                         label="操作"
                         align="center">
          <template slot-scope="scope">
            <el-button size="small" @click="openEditDialog(scope.row.domain_name,scope.row.record,scope.row.record_type,scope.row.ttl)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteRecord(scope.row.domain_name,scope.row.record,scope.row.record_type)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <el-dialog
      title="新增域名"
      :visible.sync="addRecordVisible"
      width="50%">
      <div>
        <div class="input-label">新增域名</div>
        <el-input class="large-input" size="large" v-model="addRecordName" placeholder="新增域名" @blur="getDefaultTTL"></el-input>
        <el-button size="large" type="primary" style="margin-left: 10px"  @click="addRecordSubmit">提交</el-button>
        <div class="input-div">
          <div class="input-label">自动绑定</div>
          <el-checkbox v-model="isAutoBind"/>
        </div>
        <div v-if="isAutoBind">
          <div class="input-div">
            <div class="input-label">域名子网</div>
            <el-select v-model="addRecordSubnet" clearable filterable placeholder="子网域名">
              <el-option
                v-for="item in regionOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value">
              </el-option>
            </el-select>
          </div>
        </div>
        <div v-if="!isAutoBind">
          <div class="input-div">
            <div class="input-label">记录类型</div>
            <el-select class="medium-input" v-model="addRecordType">
              <el-option
                v-for="item in recordTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value">
              </el-option>
            </el-select>
            <el-checkbox v-model="isCheckRecord"></el-checkbox>
            <span v-if="addRecordType==='CNAME'" class="input-label">检查CNAME</span>
            <span v-if="addRecordType==='A' || addRecordType==='AAAA'" class="input-label">检查IP</span>
          </div>
          <div class="input-div">
            <div class="input-label">域名记录</div>
            <el-input class="large-input" placeholder="请输入域名记录" v-model="addRecordValue"/>
          </div>
          <div class="input-div">
            <div class="input-label">域名TTL</div>
            <el-input class="medium-input" placeholder="请输入TTL" v-model="addRecordTtl" />
          </div>
          <div class="input-div">
            <div class="input-label">默认TTL</div>
            <el-input class="medium-input" placeholder="默认TTL" v-model="defaultTTL" :disabled="true" />
          </div>
        </div>
      </div>
      <div class="tip">
        <div>说明:</div>
        <div style="color: red">1、可添加多条A/AAAA记录，只能添加一条CNAME记录，两种记录不能并存。</div>
        <div style="color: red">2、取消勾选检查CNMAE后可解析到第三方域名。</div>
        <div style="color: red">3、取消勾选检查IP后可解析到非ippool中的IP。</div>
        <div>4、TTL为0时，使用全局TTL配置。</div>
        <div>5、自动绑定需要指定子网。</div>
      </div>
    </el-dialog>
    <el-dialog
      title="记录修改"
      :visible.sync="editDialogVisible"
      width="50%">
      <div>
        <div class="input-div">
          <div class="input-label">域名</div>
          <el-input class="large-input" v-model="editName" :disabled="true"></el-input>
        </div>
        <div class="input-div">
          <div class="input-label">类型</div>
          <el-select class="medium-input" v-model="editRecord.record_type">
            <el-option
                v-for="item in recordTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value">
              </el-option>
          </el-select>
          <el-checkbox v-model="editRecord.check"></el-checkbox>
          <span v-if="editRecord.record_type==='CNAME'" class="input-label">检查CNAME</span>
          <span v-if="editRecord.record_type==='A' || editRecord.record_type==='AAAA'" class="input-label">检查IP</span>
        </div>
        <div class="input-div">
          <div class="input-label">记录</div>
          <el-input class="large-input" placeholder="请输入记录" v-model="editRecord.record" />
        </div>
        <div class="input-div">
          <div class="input-label">TTL</div>
          <el-input class="large-input" placeholder="请输入TTL" v-model="editRecord.ttl"/>
        </div>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="modifyRecord">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'AddRecord',
    data () {
      return {
        typeOptions: [{
          label: '域名',
          value: 'domain'
        }, {
          label: '解析',
          value: 'record'
        }],
        recordTypeOptions: [{
          label: 'A',
          value: 'A'
        }, {
          label: 'AAAA',
          value: 'AAAA'
        }, {
          label: 'CNAME',
          value: 'CNAME'
        }],
        searchType: 'domain',
        searchCondition: '',
        recordList: [],

        // 普通记录相关
        addRecordVisible: false,
        regionOptions: [],
        zonesTTL: {},
        defaultTTL: '',
        addRecordName: '',
        addRecordType: 'A',
        addRecordValue: '',
        addRecordTtl: 0,
        addRecordSubnet: '',
        isAutoBind: false,
        isCheckRecord: true,

        editDialogVisible: false,
        editName: '',
        originRecord: {},
        editRecord: {}
      }
    },

    mounted () {
      this.fetchRegionNames()
      this.fetchZonesTTL()
    },

    methods: {
      fetchRegionNames () {
        util.get(this, {
          url: '/web/subnet/list/region',
          succ: (data) => {
            this.regionOptions = util.objArrayToOptions(data.data, 'region_name', 'region_name')
          }
        })
      },

      fetchZonesTTL () {
        util.get(this, {
          url: '/web/record/list/zone_ttl',
          succ: (data) => {
            this.zonesTTL = data.data
          }
        })
      },

      searchGeneral () {
        // 默认按ip搜索
        let param = {record: this.searchCondition}
        if (this.searchType === 'domain') {
          param = {domain_name: this.searchCondition}
        }
        util.get(this, {
          url: '/web/record/get/domain_records',
          data: param,
          succ: (data) => {
            console.log(data.data)
            this.recordList = data.data
          }
        })
      },

      getDefaultTTL () {
        this.addRecordName = this.addRecordName.trim()
        if (this.addRecordName === '') {
          return false
        }
        this.defaultTTL = 0
        let tags = this.addRecordName.split('.')
        for (let i in tags) {
          if (i !== 0) {
            let zone = tags.slice(i).join('.')
            if (zone in this.zonesTTL) {
              this.defaultTTL = this.zonesTTL[zone]
              console.log(zone)
              break
            }
          }
        }
        if (this.defaultTTL === 0) {
          util.notify(this, '警告', '没有适配的zone', 'warning')
        }
      },

      addRecordSubmit () {
        this.addRecordName = this.addRecordName.trim()
        this.addRecordValue = this.addRecordValue.trim()
        if (this.addRecordName === '') {
          util.notify(this, '错误', '域名为空！', 'error')
          return false
        }
        if (this.isAutoBind) {
          if (this.addRecordSubnet === '') {
            util.notify(this, '错误', '子网为空', 'error')
            return false
          }
        } else {
          if (this.addRecordValue === '') {
            util.notify(this, '错误', '域名记录为空！', 'error')
            return false
          }
        }
        this.$confirm('是否新增' + this.addRecordName + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.searchType = 'domain'
          this.searchCondition = this.addRecordName
          let url = '/web/record/manually_add_record'
          let param = {domain: this.addRecordName, record: this.addRecordValue, record_type: this.addRecordType, ttl: this.addRecordTtl, check_record: this.isCheckRecord}
          if (this.isAutoBind) {
            url = 'web/record/auto_add_record'
            param = {domain: this.addRecordName, region: this.addRecordSubnet}
          }
          util.post(this, {
            url: url,
            data: param,
            succ: (data) => {
              util.notify(this, '成功', '新增域名成功')
              this.addRecordVisible = false
              this.searchGeneral()
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消新增域名'
          })
        })
      },

      openEditDialog (name, record, type, ttl) {
        this.editDialogVisible = true
        this.editName = name
        this.originRecord = {domain_name: name, record: record, record_type: type, ttl: ttl}
        this.editRecord = {domain_name: name, record: record, record_type: type, ttl: ttl, check: true}
      },

      modifyRecord () {
        let update = {}
        this.editRecord.record = this.editRecord.record.trim()
        if (this.editRecord.record === '') {
          util.notify(this, '错误', '记录不能为空', 'error')
          return false
        }
        this.editRecord.ttl = parseInt(this.editRecord.ttl)
        if (typeof this.editRecord.ttl !== 'number' || this.editRecord.ttl < 0) {
          util.notify(this, '错误', 'TTL必须是大于0的整数', 'error')
          return false
        }
        if (this.editRecord.record === this.originRecord.record && this.originRecord.record_type !== this.editRecord.record_type) {
          util.notify(this, '错误', '记录类型错误', 'error')
          return false
        }

        if (this.editRecord.record !== this.originRecord.record) {
          update['record_type'] = this.editRecord.record_type
          update['record'] = this.editRecord.record
          update['check_record'] = this.editRecord.check
        }
        if (this.editRecord.ttl !== this.originRecord.ttl) {
          update['ttl'] = this.editRecord.ttl
        }
        if (JSON.stringify(update) === '') {
          util.notify(this, '错误', '请输入修改信息', 'error')
        }
        console.log(update)

        this.$confirm('是否修改' + name + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/record/modify_record',
            data: {domain_name: this.editName, origin_record: this.originRecord.record, update_dict: update},
            succ: (data) => {
              util.notify(this, '成功', '修改记录成功')
              this.editDialogVisible = false
              this.searchGeneral()
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消修改'
          })
        })
      },

      deleteRecord (name, records, type) {
        this.$confirm('是否删除' + name + '?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/record/delete',
            data: {domain_name: name, record: records, record_type: type},
            succ: (data) => {
              util.notify(this, '成功', '删除记录成功')
              this.searchGeneral()
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
  .input-div {
    margin-top: 15px ;
  }

  .input-label {
    display: inline-block;
    width: 100px;
    margin-right: 10px;
  }

  .tip {
    color: blue;
    margin-top: 30px
  }
</style>
