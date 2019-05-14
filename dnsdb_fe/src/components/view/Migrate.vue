<template>
  <div class="migrate">
    <div class="tab-panel">
      <el-row>
        <el-col :span="15"><div>
          <el-form :inline="true" class="demo-form-inline">
            <el-form-item label="迁移机房" size="small">
              <el-select v-model="srcRoomsChecked" multiple clearable 
                :collapse-tags="srcRoomsChecked.length > 6">
                <el-option
                    v-for="item in ColoOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="运营商"  size="small">
              <el-select v-model="ispsChecked" multiple clearable 
                :collapse-tags="ispsChecked.length > 4"
                @change="handleMigrateIspChange">
                <el-option
                    v-for="item in IspOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="目的机房" size="small">
              <el-select v-model="dstRoomsChecked" multiple clearable>
                <el-option
                  v-for="item in ColoOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                  :disabled="srcRoomsChecked.indexOf(item.value) >= 0">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item size="small">
              <el-button type="primary" @click="listMigrateDomain">预览</el-button>
            </el-form-item>
            <el-form-item size="small">
              <el-button type="primary" @click="migrateRooms">迁移</el-button>
            </el-form-item>
          </el-form>
        </div></el-col>
        <el-col :span="8"><div>
          <el-button size="small" type="danger" style="margin-left: 20px" @click="onekeyRecoverRooms">
            一键恢复
          </el-button>
        </div></el-col>
      </el-row>
    </div>
    <div class="tab-panel" v-if="showTable === 'domains'">
      <el-table
        border
        key="migrateDomainList"
        v-loading="migrateListLoading"
        :data="migrateDomainList">
        <el-table-column prop="domain_name"
                          label="域名"
                          width="400px"
                          align="center"/>
        <el-table-column prop="cur"
                          label="需迁移机房"
                          width="200px"
                          align="center"/>
        <el-table-column prop="after"
                          label="迁移后机房"
                          width="200px"
                          align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.after===''" style="color: red">无迁移机房</span>
            <span v-else style="color: green">{{scope.row.after}}</span>
          </template>
        </el-table-column>
        <el-table-column prop="isps"
                          label="迁移运营商"
                          width="300px"
                          align="center">
          <template slot-scope="scope">
            <span class="isp" v-for="isp in scope.row.isps">
              {{ isp }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="tab-panel" v-if="showTable === 'history'">
      <el-table
        border
        key="migrateHistoryInfo"
        v-loading="migrateListLoading"
        :data="migrateHistoryInfo">
        <el-table-column
          label="迁移机房"
          prop="migrate_rooms">
          <template slot-scope="scope">
            <span v-for="room in scope.row.migrate_rooms" :key="room">
              {{ room }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="迁移运营商"
          prop="migrated">
          <template slot-scope="scope">
            <span v-for="isp in scope.row.migrate_isps" :key="isp">
              {{ isp }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="目标机房"
          prop="dst_rooms">
          <template slot-scope="scope">
            <span v-for="room in scope.row.dst_rooms" :key="room">
              {{ room }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="state"
          label="状态"
          width="120px"
          align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.state==='migrating'" style="color: brown">迁移中</span>
            <span v-if="scope.row.state==='error'" style="color: red">异常</span>
            <span v-if="scope.row.state==='migrated'" style="color: green">迁移完成</span>
            <span v-if="scope.row.state==='recovered'" style="color: green">已恢复</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="progress"
          label="进度"
          width="300px"
          align="center">
          <template slot-scope="scope">
            <el-progress  :stroke-width="18" :text-inside="true"
                          :percentage="Math.round(100*(scope.row.cur/scope.row.all))"
                          :status="getStatus(scope.row.cur,scope.row.all,scope.row.state)"></el-progress>
          </template>
        </el-table-column>
        <el-table-column
            label="操作"
            align="center">
            <template slot-scope="scope">
              <el-button size="small" @click="viewPagedDetail(scope.row.id)">
                详情
              </el-button>
            </template>        
          </el-table-column>
      </el-table>
    </div>
    <div class="tab-panel" v-if="showTable === 'ispstatus'">
      <el-table
        border
        :data="ispStatus">
        <el-table-column prop="room"
                          label="机房"
                          align="center"/>
        <el-table-column prop="isp"
                          label="运营商"
                          align="center">
        </el-table-column>
        <el-table-column prop="is_health"
              label="状态"
              align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.is_health" style="color: green">正常</span>
            <span v-else style="color: red">维护</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time"
                          label="维护时间"
                          align="center">
        </el-table-column>
      </el-table>
    </div>
    <el-dialog
      title="迁移详情"
      :visible.sync="detailDialogVisible"
      width="90%">
      <el-row :gutter="0" type="flex" >
        <el-col :span="20">
          <span>目标机房：</span>
          <span>{{ migrateRules }}</span>
        </el-col>
        <el-col :span="4" style="text-align: right">
          <el-input class="medium-input" placeholder="请输入域名" v-model="detailDomain"/>
          <el-button type="info" @click="viewPagedDetail">搜索</el-button>
        </el-col>
      </el-row>
      <el-table
        style="margin-top: 5px"
        :data="migrateDetails">
        <el-table-column prop="domain_name"
                         label="域名"
                         width="350px"
                         align="center"/>
        <el-table-column prop="isp"
                         label="运营商"
                         width="150px"
                         align="center"/>
        <el-table-column prop="before_enabled_server_rooms"
                         label="迁移前"
                         align="center"/>
        <el-table-column prop="after_enabled_server_rooms"
                         label="迁移后"
                         align="center"/>
      </el-table>
      <el-pagination
        align="right"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-size="pageSize"
        :total="total">
      </el-pagination>
    </el-dialog>
    <el-dialog
      title="迁移进度"
      :visible.sync="migrateProcessDialogVisible"
      width="60%">
      <el-table
        :data="migrateHistoryInfo"
        style="width: 100%">
        <el-table-column
          label="迁移机房"
          prop="migrate_rooms">
          <template slot-scope="scope">
            <span v-for="room in scope.row.migrate_rooms" :key="room">
              {{ room }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="迁移运营商"
          prop="migrated">
          <template slot-scope="scope">
            <span v-for="isp in scope.row.migrate_isps" :key="isp">
              {{ isp }}
            </span>
          </template>
        </el-table-column>
        <el-table-column
          label="目标机房"
          prop="dst_rooms">
          <template slot-scope="scope">
            <span v-for="room in scope.row.dst_rooms" :key="room">
              {{ room }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="state"
          label="状态"
          width="120px"
          align="center">
          <template slot-scope="scope">
            <span v-if="scope.row.state==='migrating'" style="color: brown">迁移中</span>
            <span v-if="scope.row.state==='error'" style="color: red">异常</span>
            <span v-if="scope.row.state==='migrated'" style="color: green">迁移完成</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="progress"
          label="进度"
          width="300px"
          align="center">
          <template slot-scope="scope">
            <el-progress  :stroke-width="18" :text-inside="true"
                          :percentage="Math.round(100*(scope.row.cur/scope.row.all))"
                          :status="getStatus(scope.row.cur,scope.row.all,scope.row.state)"></el-progress>
          </template>
        </el-table-column>
      </el-table>
      <div slot="footer" class="dialog-footer">
        <el-button @click="migrateProcessDialogVisible = false; migrateHistoryInfo = []">关闭</el-button>
        <el-button type="primary" @click="migrateProcessDialogVisible = false; migrateHistoryInfo = []">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  let domain = '/web/view/'
  export default {
    name: 'Migrate',
    data () {
      return {
        showTable: '',
        ColoOptions: [],
        IspOptions: [],
        srcRoomsChecked: [],
        ispsChecked: [],
        dstRoomsChecked: [],
        allIsps: [],
        ispStatus: [],
        migrateDomainList: [],
        spanObj: {},
        migrateListLoading: false,

        migrateProcessDialogVisible: false,
        migrateHistoryInfo: [],
        migrateDone: false,
        migtateOperation: '',
        ispTransDict: {},

        migrateHistory: [],
        detailDialogVisible: false,
        page: 1,
        pageSize: 18,
        total: 0,
        detailDomain: '',
        migrateId: 0,
        migrateDetails: [],
        migrateRules: '',
        autoRecover: false,

        intervalId: -1,
        getIspStatusInterval: -1,
        getMigrateInfoInterval: -1,
        freshHistory: false
      }
    },
    mounted () {
      this.fetchServerRooms()
      this.fetchIsp()
      this.fetchMigrateHistory()
      this.intervalId = setInterval(() => {
        if (this.showTable === 'history' && this.freshHistory) {
          this.fetchMigrateHistory()
        }
      }, 2000)

      this.getMigrateInfoInterval = setInterval(() => {
        if (this.migrateHistoryInfo !== [] && this.migrateProcessDialogVisible && this.migrateHistoryInfo[0].state !== 'done') {
          this.getMigrateInfo()
        }
      }, 2000)
    },

    destroyed () {
      clearInterval(this.intervalId)
      clearInterval(this.getMigrateInfoInterval)
    },

    methods: {
      fetchIsp () {
        util.get(this, {
          url: domain + 'list/isp',
          succ: (data) => {
            this.IspOptions = [{label: '全选', value: 'all'}]
            this.allIsps = []
            this.ispTransDict = {}
            let isps = data.data
            for (let i in isps) {
              let isp = isps[i]
              let item = {}
              item.label = isp.name_in_chinese
              item.value = isp.name_in_english
              this.IspOptions.push(item)
              this.ispTransDict[isp.name_in_english] = isp.name_in_chinese
              this.allIsps.push(isp.name_in_english)
            }
            this.IspOptions.push({label: '清除', value: 'clear'})
          }
        })
      },

      fetchServerRooms () {
        util.get(this, {
          url: domain + 'list/server_room',
          succ: (data) => {
            this.ColoOptions = util.arrayToOptions(data.data)
          }
        })
      },

      handleMigrateIspChange () {
        if (this.ispsChecked.indexOf('all') !== -1) {
          this.ispsChecked = this.allIsps
        } else if (this.ispsChecked.indexOf('clear') !== -1) {
          this.ispsChecked = []
        }
      },

      clearMigrateParams () {
        this.srcRoomsChecked = []
        this.ispsChecked = []
      },

      listMigrateDomain () {
        if (this.srcRoomsChecked.length === 0 || this.ispsChecked.length === 0 || this.dstRoomsChecked.length === 0) {
          this.$message.warning('参数不能为空')
          return
        }
        this.migrateListLoading = true
        this.showTable = 'domains'
        util.post(this, {
          url: domain + 'list_migrate_domain',
          data: {src_rooms: this.srcRoomsChecked, dst_rooms: this.dstRoomsChecked, isps: this.ispsChecked},
          succ: (data) => {
            this.migrateDomainList = data.data
            this.migrateListLoading = false
          }
        })
        this.migrateListLoading = false
      },

      arraySpanMethod ({row, column, rowIndex, columnIndex}) {
        if (columnIndex === 0) {
          if (rowIndex in this.spanObj) {
            return this.spanObj[rowIndex]
          } else {
            return [0, 0]
          }
        }
      },

      fetchMigrateHistory () {
        this.showTable = 'history'
        this.freshHistory = false
        util.get(this, {
          url: domain + 'list/migrate_history',
          succ: (data) => {
            this.migrateHistoryInfo = data.data
            for (let item of this.migrateHistoryInfo) {
              if (item.state === 'migrating') {
                this.freshHistory = true
                break
              }
            }
          }
        })
      },

      migrateRooms () {
        if (this.srcRoomsChecked.length === 0 || this.ispsChecked.length === 0 || this.dstRoomsChecked.length === 0) {
          this.$message.warning('参数不能为空')
          return
        }
        this.$confirm('是否开始迁移', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: domain + 'migrate_rooms',
            data: {src_rooms: this.srcRoomsChecked, dst_rooms: this.dstRoomsChecked, isps: this.ispsChecked},
            succ: (data) => {
              util.notify(this, '成功', '机房迁移成功')
              this.fetchMigrateHistory()
              return
            }
          })
        }).catch(() => {
          this.$message.info('取消迁移')
        })
      },

      getMigrateInfo () {
        util.get(this, {
          url: domain + 'get/migrate_info',
          data: {history_id: this.migrateHistoryInfo[0].id},
          succ: (data) => {
            this.migrateHistoryInfo = data.data
          }
        })
      },

      onekeyRecoverRooms () {
        this.$confirm('是否一键恢复所有已迁移机房', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: domain + 'onekey_recover_rooms',
            succStr: '一键恢复成功'
          })
        }).catch(() => {
          this.$message.info('取消一键恢复')
        })
        this.freshHistory = true
      },

      viewPagedDetail (migrateId) {
        this.migrateId = migrateId
        this.detailDomain = ''
        util.get(this, {
          url: domain + 'get/view_migrate_detail',
          data: {migrate_id: migrateId, page: this.page, page_size: this.pageSize, domain: this.detailDomain},
          succ: (data) => {
            this.migrateDetails = data.data.detail
            this.total = data.data.total
            this.detailDialogVisible = true
            this.migrateRules = data.data.migrate_rules
          }
        })
      },

      getStatus (cur, all, state) {
        if (state === 'error') {
          return 'exception'
        } else if (cur === all) {
          return 'success'
        } else {
          return ''
        }
      },

      handleCurrentChange (val) {
        this.page = val
        this.viewPagedDetail()
      }
    }
  }
</script>

<style scoped>
  .el-row {
    margin-bottom: 20px;
  }
  .el-col {
    border-radius: 4px;
  }
  .grid-content {
    border-radius: 4px;
    min-height: 36px;
  }
  hr {
    border-top:1px;
    margin-top: 20px;
  }
  .tab-panel {
    background: white;
    padding-left: 20px;
    padding-right: 20px;
    padding-top: 10px;
    padding-bottom: 10px;
  }
  .migrate {
   background: white;
   height: 100%;
  }

  .isp {
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

  .center-in-center{
    position: absolute;
    left: 50%;
    -webkit-transform: translate(-50%, 0);
    -moz-transform: translate(-50%, 0);
    -ms-transform: translate(-50%, 0);
    -o-transform: translate(-50%, 0);
    transform: translate(-50%, 0);
  }
</style>
