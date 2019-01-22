<template>
  <div style="background: white">
    <div class="condition-div">
      <el-input class="medium-input" v-model="domain" placeholder="域名" @keyup.enter.native="fetchDnsLog"></el-input>
      <el-select class="medium-input" v-model="type" placeholder="类型" @change="fetchDnsLog">
        <el-option
          v-for="item in typeOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value">
        </el-option>
      </el-select>
      <el-input class="medium-input" v-model="rtx_id" placeholder="操作人" @keyup.enter.native="fetchDnsLog"></el-input>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        :picker-options="pickerOptions"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="yyyy-MM-dd"
        @change="changeDateRange"
        align="right">
      </el-date-picker>
      <el-button type="info" @click="fetchDnsLog">搜索</el-button>
      <el-button style="margin-left: 0px" type="warning" @click="clearCondition">清除</el-button>
    </div>
    <div align="center">
      <el-table
        :data="dnsLog"
        class="dnslog-table"
        element-loading-text="加载中"
        border>
        <el-table-column prop="rtx_id"
                         label="操作者"
                         width="150"
                         align="center"/>
        <el-table-column prop="op_type"
                         label="类型"
                         width="150"
                         align="center">
          <template slot-scope="scope">
              <span>{{ typeObj[scope.row.op_type] }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="op_domain"
                         label="域名"
                         width="250"
                         align="center"/>
        <el-table-column prop="op_before"
                         label="操作前"
                         align="center">
          <template slot-scope="scope">
            <div  align="left" v-for="item in scope.row[scope.column.property]">
                {{ item }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="op_after"
                         label="操作后"
                         align="center">
          <template slot-scope="scope">
            <div  align="left" v-for="item in scope.row[scope.column.property]">
              <span v-if="item.startsWith('http')">
                <a :href="item">gitlab链接</a>
              </span>
              <span v-else>
                {{ item }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="op_time"
                         label="操作时间"
                         width="180"
                         align="center"/>
        <el-table-column prop="op_result"
                         label="结果"
                         width="80"
                         align="center">
          <template slot-scope="scope">
              <span v-if="scope.row.op_result==='ok'" style="color: green">成功</span>
              <span v-else-if="scope.row.op_result==='start'" style="color: brown">进行中</span>
              <span v-else-if="scope.row.op_result==='wait'" style="color: brown">等待</span>
              <span v-else-if="scope.row.op_type==='conf_deploy'" style="color: red" @click="retryDeploy(scope.row.id)">重试</span>
              <span v-else style="color: red;cursor: pointer" @click="getFailDetail(scope.row.id)">失败</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        align="right"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-size="pageSize"
        :total="total">
      </el-pagination>
    </div>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  let domain = '/web/preview/'
  export default {
    name: 'DnsLog',
    data () {
      return {
        dateRange: [],
        start: '',
        end: '',
        pickerOptions: {
          shortcuts: [{
            text: '最近一周',
            onClick (picker) {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
              picker.$emit('pick', [start, end])
            }
          }, {
            text: '最近一个月',
            onClick (picker) {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
              picker.$emit('pick', [start, end])
            }
          }, {
            text: '最近三个月',
            onClick (picker) {
              const end = new Date()
              const start = new Date()
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
              picker.$emit('pick', [start, end])
            }
          }]
        },
        dnsLog: [],
        page: 1,
        pageSize: 30,
        domain: '',
        rtx_id: '',
        type: '',
        total: 0,
        typeObj: {},
        filedObj: {},
        typeOptions: [],

        logMap: {},
        updateLog: false,
        intervalId: -1
      }
    },
    mounted () {
      this.fetchOperationConstant()
      this.fetchDnsLog()
      this.intervalId = setInterval(() => {
        console.log(this.updateLog)
        if (this.updateLog) {
          this.fetchDnsLog()
        }
      }, 2000)
      // this.initMap()
    },

    destroyed () {
      clearInterval(this.intervalId)
    },

    methods: {
      sortTypeOption (a, b) {
        return a.label < b.label
      },

      fetchOperationConstant () {
        util.get(this, {
          url: domain + 'list/operation_constant',
          succ: (data) => {
            this.typeObj = data.data.type_dict
            this.typeOptions = util.objToOptions(this.typeObj).sort(this.sortTypeOption)
            this.filedObj = data.data.filed_dict
          }
        })
      },

      initMap () {
        // this.logMap['update_domain_status'] = this.formatUpdateStatusLog
      },

      clearCondition () {
        this.start = ''
        this.end = ''
        this.page = 1
        this.pageSize = 30
        this.domain = ''
        this.type = ''
        this.rtx_id = ''
        this.dateRange = []
        this.fetchDnsLog()
      },

      retryDeploy (id) {
        this.$confirm('是否重试该任务', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: domain + 'retry_deploy_job',
            data: {deploy_id: id},
            succ: (data) => {
              util.notify(this, '成功', '重试成功', 'success')
              this.fetchDnsLog()
            }
          })
        }).catch(() => {
          this.$message.info('取消重试部署任务')
        })
      },

      getFailDetail (id) {
        util.get(this, {
          url: domain + 'get/dns_log_detail',
          data: {id: id},
          succ: (data) => {
            if (data.data !== null) {
              this.$alert(data.data, '错误详情', {
                confirmButtonText: '确定'
              })
            }
          }
        })
      },

      fetchDnsLog () {
        let condition = {
          page: this.page,
          page_size: this.pageSize,
          start_time: this.start,
          end_time: this.end
        }
        if (this.domain !== '') {
          condition['domain'] = this.domain
        }
        if (this.type !== '') {
          condition['type'] = this.type
        }
        if (this.rtx_id !== '') {
          condition['rtx_id'] = this.rtx_id
        }
        util.get(this, {
          url: domain + 'list/operation_log',
          data: condition,
          succ: (data) => {
            // console.log(data.data.logs)
            this.formatLog(data.data.logs)
            this.dnsLog = data.data.logs
            this.total = data.data.total
          }
        })
      },

      changeDateRange (value) {
        this.start = value[0]
        this.end = value[1]
      },

      handleCurrentChange (val) {
        this.page = val
        this.fetchDnsLog()
      },

      arrayFileds (filedsStr) {
        let array = []
        if (filedsStr !== '{}') {
          let filedObj = JSON.parse(filedsStr)
          for (let i in filedObj) {
            let value = filedObj[i]
            if (JSON.stringify(value).startsWith('{')) {
              let inner = []
              for (let k in value) {
                if (k in this.filedObj) {
                  k = this.filedObj[k]
                }
                inner.push(k + ': ' + value[k])
              }
              value = inner.toString()
            }
            if (i in this.filedObj) {
              i = this.filedObj[i]
            }
            array.push(i + ': ' + value)
          }
        }
        return array
      },

      generalFormat (item) {
        item.op_before = this.arrayFileds(item.op_before)
        item.op_after = this.arrayFileds(item.op_after)
      },

      formatLog (list) {
        this.updateLog = false
        for (let i in list) {
          let item = list[i]
          if (item.op_result === 'wait' || item.op_result === 'start') {
            this.updateLog = true
          }
          if (this.logMap[item.op_type] === undefined) {
            this.generalFormat(item)
            continue
          }
          this.logMap[item.op_type](item)
        }
      },

      format (item) {
        item.op_before = JSON.parse(item.op_before)
        item.op_after = JSON.parse(item.op_after)
        // 格式化op_before
        let beforeList = []
        let afterList = []
        for (let x = 0; x < item.op_before.length; x++) {
          let before = ''
          let state = item.op_before[x]
          before += (state.isp_name + ': ')
          let rooms = []
          for (let p in state.state) {
            if (p === 'cdn') {
              rooms.push(state.state.cdn)
            } else {
              rooms.push(p)
            }
          }
          rooms = rooms.sort()
          before += rooms.join(',')
          beforeList.push(before)
        }
        // 格式化op_after
        for (let x = 0; x < item.op_after.length; x++) {
          let after = ''
          let state = item.op_after[x]
          after += (state.isp_name + ': ')
          let rooms = []
          for (var p in state.state) {
            if (p === 'cdn') {
              rooms.push(state.state.cdn)
            } else {
              rooms.push(p)
            }
          }
          rooms = rooms.sort()
          after += (rooms.join(','))
          afterList.push(after)
        }
        item.op_before = beforeList
        item.op_after = afterList
      }
    }
  }
</script>

<style scoped>

  .condition-div {
    padding-left: 10px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

</style>
