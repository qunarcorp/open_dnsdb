<template>
  <div>
    <div>
      <el-tabs v-model="ipActiveName"  @tab-click="handleIpTabClick">
        <el-tab-pane label="操作" name="operation">
          <div class="tab-panel">
            <el-input class="large-input" size="large" placeholder="请输入ip" v-model="ipSearch"
                      @keyup.enter.native="searchIp"/>
            <el-button size="large" @click="searchIp">搜索</el-button>
            <el-button v-if="ipStateList.length!==0&&canOff" size="large" type="warning" @click="switchIpToAqb" >切换高防</el-button>
            <el-button v-if="ipStateList.length!==0&&canOff" size="large" type="danger" @click="replaceIp">替换IP</el-button>
          </div>
          <div class="tab-panel">
            <el-table
              class="medium-table"
              v-loading="searchIpLoading"
              border
              :data="ipStateList">
              <el-table-column prop="domain_name"
                               label="域名"
                               width="300px"
                               align="center"/>
              <el-table-column
                prop="active"
                label="IP激活运营商"
                align="center">
                <template slot-scope="scope">
                      <span class="table-item" v-for="isp in scope.row.active">
                        {{ isp }}
                      </span>
                  <span v-if="scope.row.active.length===0">
                        未激活
                      </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="has_aqb"
                label="高防配置"
                width="100px"
                align="center">
                <template slot-scope="scope">
                      <span v-if="scope.row.has_aqb">
                        有
                      </span>
                  <span v-else style="color: red">
                        无
                      </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="only_record"
                label="唯一解析"
                width="100px"
                align="center">
                <template slot-scope="scope">
                      <span v-if="scope.row.only_record" style="color:red;">
                        是
                      </span>
                  <span v-else >
                        否
                      </span>
                </template>
              </el-table-column>
              <el-table-column
                prop="has_switched"
                label="替换状态"
                width="100px"
                align="center">
                <template slot-scope="scope">
                      <span v-if="scope.row.has_switched==='forbid'" style="color:red;">
                        已禁用
                      </span>
                  <span v-if="scope.row.has_switched==='replace'" style="color: red">
                        已替换
                      </span>
                  <span v-if="scope.row.has_switched==='no_switch'" >
                        无
                      </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane class="tab-panel" label="记录" name="record">
          <el-table
            border
            :data="switchHistory">
            <el-table-column prop="id"
                             label="序号"
                             width="80px"
                             align="center"/>
            <el-table-column prop="rtx_id"
                             label="操作人"
                             width="150px"
                             align="center"/>
            <el-table-column prop="update_at"
                             label="时间"
                             width="200px"
                             align="center"/>
            <el-table-column prop="switch_ip"
                             label="切换IP"
                             width="240px"
                             align="center"/>
            <el-table-column prop="switch_type"
                             label="操作类型"
                             width="240px"
                             align="center">
              <template slot-scope="scope">
                <span v-if="scope.row.switch_type==='aqb'">切换高防</span>
                <span v-if="scope.row.switch_type==='replace'&&scope.row.switch_to===''">禁用IP</span>
                <span v-if="scope.row.switch_type==='replace'&&scope.row.switch_to!==''">替换IP</span>
              </template>
            </el-table-column>
            <el-table-column prop="switch_to"
                             label="切换后"
                             width="200px"
                             align="center">
              <template slot-scope="scope">
                <span v-if="scope.row.switch_to==='aqb'">高防配置</span>
                <span v-if="scope.row.switch_type==='replace'&&scope.row.switch_to===''">禁用IP</span>
                <span v-if="scope.row.switch_type==='replace'&&scope.row.switch_to!==''">{{scope.row.switch_to}}</span>
              </template>
            </el-table-column>
            <el-table-column prop="state"
                             label="切换状态"
                             align="center">
              <template slot-scope="scope">
                <span v-if="scope.row.state==='switched'" style="color: blue">已切换</span>
                <span v-if="scope.row.state==='recovered'">已恢复</span>
              </template>
            </el-table-column>>
            <el-table-column prop="operation"
                             label="操作"
                             width="250px"
                             align="center">
              <template slot-scope="scope">
                <el-button size="small"
                           v-if="scope.row.state==='switched'&&scope.row.switch_type==='aqb'"
                           type="info"
                           :disabled="scope.row.state==='recovered'"
                           @click="switchIpFromAqb(scope.row.id)">
                  取消高防
                </el-button>
                <el-button size="small"
                           v-if="scope.row.state==='switched'&&scope.row.switch_type==='replace'&&scope.row.switch_to!==''"
                           type="info" :disabled="scope.row.state==='recovered'"
                           @click="cancelReplaceIp(scope.row.id)">
                  取消替换
                </el-button>
                <el-button size="small"
                           v-if="scope.row.state==='switched'&&scope.row.switch_type==='replace'&&scope.row.switch_to===''"
                           type="info" :disabled="scope.row.state==='recovered'"
                           @click="cancelReplaceIp(scope.row.id)">
                  取消禁用
                </el-button>
                <el-button size="small"
                           v-if="scope.row.switch_type==='aqb'"
                           @click="viewSwitchDetail(scope.row.id)">
                  查看
                </el-button>
                <span v-if="scope.row.state==='recovered'&&scope.row.switch_type==='replace'">无操作</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    <el-dialog
      title="高防配置切换"
      :visible.sync="aqbVisible">
    <span>
      <div v-if="noAqbList.length===0">切换成功！</div>
      <div v-if="noAqbList.length!==0">以下域名高防未配置：</div>
      <div v-for="domain in noAqbList">
        <div style="width:30px;margin-top: 5px;">{{domain}}</div>
      </div>
    </span>
      <span slot="footer" class="dialog-footer">
      <el-button type="primary" @click="handleCloseAqbDialog">确定</el-button>
    </span>
    </el-dialog>
    <el-dialog
      title="IP替换"
      :visible.sync="ipVisible">
      <el-input style="display: inline-block" v-model="switchTo" placeholder="请输入替换ip,为空即禁用该IP."></el-input>
      <span slot="footer" class="dialog-footer">
      <el-button type="primary" @click="handleCloseIpDialog">替换</el-button>
    </span>
    </el-dialog>
    <el-dialog
      title="切换详情"
      :visible.sync="detailVisible"
      width="90%">
      <el-table
        style="margin-top: 5px"
        :data="switchDetails">
        <el-table-column prop="domain_name"
                         label="域名"
                         width="350px"
                         align="center"/>
        <el-table-column prop="isp"
                         label="运营商"
                         width="150px"
                         align="center"/>
        <el-table-column prop="before_enabled_server_rooms"
                         label="切换前机房"
                         align="center"/>
        <el-table-column prop="before_state"
                         label="切换前状态ID"
                         align="center"/>
        <el-table-column prop="after_state"
                         label="切换后状态ID"
                         align="center"/>
      </el-table>
      <el-pagination
        align="right"
        layout="prev, pager, next"
        @current-change="handleDetailChange"
        :current-page="detailPage"
        :page-size="detailPageSize"
        :total="detailTotal">
      </el-pagination>
    </el-dialog>
  </div>
</template>

<script>
  let domain = ''
  export default {
    name: 'IpManager',
    data () {
      return {
        ipActiveName: 'operation',

        ipSearch: '',
        searchIpLoading: false,
        ipStateList: [],
        canOff: false,
        aqbVisible: false,
        ipVisible: false,
        switchTo: '',
        noAqbList: [],
        switchHistory: [],

        detailVisible: false,
        detailPage: 1,
        detailPageSize: 18,
        detailTotal: 0,
        switchDetails: [],
        switchId: 0,

        intervalId: -1
      }
    },

    mounted () {
      this.intervalId = setInterval(() => {
        if (this.ipActiveName === 'record') {
          this.fetchSwitchHistory()
        }
      }, 2000)
    },

    destroyed () {
      clearInterval(this.intervalId)
    },

    methods: {
      handleIpTabClick (tab, event) {
        if (tab.$data.index === '1') {
          this.fetchSwitchHistory()
        }
      },

      searchIp () {
        if (this.ipSearch === '') {
          this.$notify.error({
            title: '搜索IP失败',
            message: 'IP不能为空',
            duration: 1500
          })
          return false
        }
        this.searchIpLoading = true
        this.$http.post(domain + 'ui/list_ip_state', {ip: this.ipSearch})
          .then((res) => {
            this.ipStateList = res.data.data
            this.canOff = false
            for (let i in this.ipStateList) {
              if (this.ipStateList[i].active.length !== 0) {
                this.canOff = true
              }
            }
            this.searchIpLoading = false
          })
          .catch((err) => {
            this.searchIpLoading = false
            console.log(err)
          })
      },

      switchIpToAqb () {
        this.$confirm('是否将所有激活该ip的域名切换到高防', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.$http.post(domain + 'ui/switch_ip_to_aqb', {ip: this.ipSearch})
            .then((res) => {
              if (res.data.data === 'no_domain') {
                this.$notify.error({
                  title: '错误',
                  message: '没有可切换域名!',
                  duration: 1500
                })
              } else if (res.data.data === 'ip_switched') {
                this.$notify.error({
                  title: '错误',
                  message: 'IP已经被切换!',
                  duration: 1500
                })
              } else {
                this.noAqbList = res.data.data
                this.aqbVisible = true
              }
            })
            .catch((err) => {
              console.log(err)
              this.$notify.error({
                title: '错误',
                message: '切换错误',
                duration: 1500
              })
            })
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '已取消切换',
            duration: 1500
          })
        })
      },

      fetchSwitchHistory () {
        this.$http.get(domain + '/ui/list_switch_history')
          .then((res) => {
            this.switchHistory = res.data.data
          })
          .catch((err) => {
            console.log(err)
          })
      },

      switchIpFromAqb (switchId) {
        this.$confirm('是否取消该ip的高防配置', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.$http.post(domain + 'ui/switch_ip_from_aqb', {switch_id: switchId})
            .then((res) => {
              this.searchIp()
              this.$notify.success({
                title: '成功',
                message: '恢复成功',
                duration: 1500
              })
            })
            .catch((err) => {
              console.log(err)
              this.$notify.error({
                title: '错误',
                message: '恢复错误',
                duration: 1500
              })
            })
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '已取消恢复',
            duration: 1500
          })
        })
      },

      replaceIp () {
        if (this.ipSearch === '') {
          this.$notify.error({
            title: '错误',
            message: '替换ip为空',
            duration: 1500
          })
        } else {
          this.ipVisible = true
        }
      },

      cancelReplaceIp (switchId) {
        this.$confirm('是否取消该ip的替换', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.$http.post(domain + 'ui/cancel_replace_ip', {switch_id: switchId})
            .then((res) => {
              let msg = res.data.data
              if (msg === 'ok') {
                this.searchIp()
                this.$notify.success({
                  title: '成功',
                  message: '恢复成功',
                  duration: 1500
                })
              } else {
                this.$notify.error({
                  title: '错误',
                  message: '恢复错误',
                  duration: 1500
                })
              }
            })
            .catch((err) => {
              console.log(err)
              this.$notify.error({
                title: '错误',
                message: '恢复错误',
                duration: 1500
              })
            })
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '已取消恢复',
            duration: 1500
          })
        })
      },

      viewSwitchDetail (switchId) {
        this.switchId = switchId
        this.$http.post(domain + '/ui/view_switch_detail', {switch_id: switchId, page: this.detailPage, page_size: this.detailPageSize})
          .then((res) => {
            this.switchDetails = res.data.data
            this.detailTotal = res.data.total
            this.detailVisible = true
          })
          .catch((err) => {
            console.log(err)
            this.$notify.error({
              title: '获取记录失败',
              message: '未知错误!',
              duration: 1500
            })
          })
      },

      handleDetailChange (val) {
        this.detailPage = val
        this.viewSwitchDetail(this.switchId)
      },

      handleCloseIpDialog () {
        this.$http.post(domain + '/ui/replace_ip', {switch_ip: this.ipSearch, switch_to: this.switchTo})
          .then((res) => {
            let msg = res.data.data
            if (msg === 'ok') {
              this.$notify.success({
                title: '成功',
                message: '替换IP成功',
                duration: 1500
              })
            } else if (msg === 'ip_switched') {
              this.$notify.error({
                title: '错误',
                message: 'IP已经替换',
                duration: 1500
              })
            } else {
              this.$notify.error({
                title: '错误',
                message: 'IP替换失败',
                duration: 1500
              })
            }
            this.ipActiveName = 'record'
            this.ipVisible = false
          })
          .catch((err) => {
            this.$notify.error({
              title: '错误',
              message: '替换IP失败',
              duration: 1500
            })
            console.log(err)
            this.ipVisible = false
          })
      },

      handleCloseAqbDialog () {
        this.aqbVisible = false
        this.searchIp()
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

</style>
