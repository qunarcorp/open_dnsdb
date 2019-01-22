<template>
  <div v-loading.body="fullScreenLoading">
    <div class="tab-panel">
      <el-row>
        <el-col :span="12"><div class="grid-content">
          <el-input class="xlarge-input" v-model="domainName" size="large"  
                placeholder="请输入域名" @keyup.enter.native="viewDomainList"/>
          <el-button size="large" type="primary" icon="search"  @click="viewDomainList">搜索</el-button>
        </div></el-col>
        <el-col :span="12"><div class="grid-content">
          <el-button size="large" type="primary" @click="handleAddDomain">新增域名</el-button>
        </div></el-col>
      </el-row>
      <div class="option-div">
        <label class="option-title">机房:</label>
        <el-checkbox-group v-model="checkedServerRooms" @change="handleCheckedRoomsChange"  style="display: inline-block">
          <el-checkbox class="option-item" v-for="serverRoom in serverRooms" :label="serverRoom" :key="serverRoom">
            <span class="option-item-text">{{serverRoom}}</span>
          </el-checkbox>
        </el-checkbox-group>
        <el-checkbox class="option-item" v-model="selectCdn">
          <span class="option-item-text">CDN</span>
        </el-checkbox>
        <el-checkbox
          class="option-item"
          :indeterminate="isSeverRoomsIndeterminate"
          v-model="checkAllServerRooms"
          @change="handleCheckAllServerRoomChange">
          <span class="option-item-text">全选</span>
        </el-checkbox>
      </div>
      <div class="option-div">
        <label class="option-title">运营商:</label>
        <el-checkbox-group v-model="checkedIsps" @change="handleCheckedIspsChange"  style="display: inline-block">
          <el-checkbox  class="option-item" v-for="isp in isps" :label="isp.name_in_english" :key="isp.name_in_english" >
            <span class="option-item-text">{{isp.name_in_chinese}}</span>
          </el-checkbox>
        </el-checkbox-group>
        <el-checkbox
          class="option-item"
          :indeterminate="isIspsIndeterminate"
          v-model="checkAllIsps"
          @change="handleCheckAllIspsChange">
          <span class="option-item-text">全选</span>
        </el-checkbox>
      </div>
    </div>
    <hr />
    <div class="tab-panel">
      <el-row :gutter="0" type="flex"  >
        <el-col :span="4">
          <label class="large-title" v-if="domainList.length>0">域名列表</label>
          <div v-loading="loadingDomainList" element-loading-text="加载中">
            <div v-for="item in domainListPage" :key="item.domain" class="list-item" @click="viewDomain(item.domain)" v-text="item.domain">
            </div>
          </div>
          <div style="float: right" v-if="domainList.length>0">
            <el-pagination
              small
              layout="prev, pager, next"
              @current-change="handleCurrentChange"
              :current-page="page"
              :page-size="pageSize"
              :total="domainListTotal">
            </el-pagination>
          </div>
        </el-col>
        <el-col :span="20" style="margin-left: 10px;">
          <div v-if="stateDomainName!==''">
            <el-row :gutter="0" type="flex" >
              <el-col :span="16">
                <span class="medium-title">当前域名：{{ stateDomainName }}</span>
                <span class="medium-title" v-if="isMigrate">(已迁移)</span>
                <el-button size="large" @click="handelEditDomain">修改域名</el-button>
                <el-button size="large" type="danger" plain @click="deleteDomain">删除域名</el-button>
              </el-col>
              <el-col :span="8" style="text-align: right">
                <el-button size="large" @click="viewDomain(stateDomainName)">刷新</el-button>
                <el-button size="large" type="warning" @click="submitModify">提交</el-button>
              </el-col>
            </el-row>
            <el-table
              class="large-table"
              style="margin-top: 10px"
              v-loading="loadingDomainInfo"
              element-loading-text="加载中"
              border
              :data="stateDomainInfo">
              <el-table-column prop="info"
                               label="机房"
                               align="center">
                <template slot-scope="scope">
                  <div v-if="scope.row.info.name!=='cdn'" style="padding-top: 10px;padding-bottom: 10px">
                    <span><label>{{ scope.row[scope.column.property].name }}<br /></label></span>
                    <el-switch
                      active-text=""
                      inactive-text=""
                      v-model="scope.row[scope.column.property].is_enabled"
                      active-color="#13ce66"
                      @change="switchAll(scope.$index,scope.row[scope.column.property].is_enabled)"
                    />
                  </div>
                  <div v-else style="padding-top: 10px;padding-bottom: 10px">
                    <span><label>CDN</label></span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column v-for="isp in isps"
                               :prop="isp.name_in_english"
                               :label="isp.name_in_chinese"
                               :key ="isp.name_in_english"
                               align="center">
                <template slot-scope="scope">
                  <div v-if="scope.row.info.name!=='cdn'"
                       style="padding-top: 5px;padding-bottom: 5px">
                    <span v-for="ip in scope.row[scope.column.property].ips" :key="ip">
                      <label  >{{ ip }}<br /></label>
                    </span>
                    <el-switch
                      active-text=""
                      inactive-text=""
                      @change="switchCn(scope.column.property,scope.row[scope.column.property].is_enabled)"
                      v-model="scope.row[scope.column.property].is_enabled"
                      active-color="#13ce66"
                    />
                  </div>
                  <div v-if="scope.row.info.name==='cdn'">
                    <el-select v-model="scope.row[scope.column.property].name"
                               @change="switchCdn(scope.column.property,scope.row[scope.column.property].name)"
                               placeholder="请选择">
                      <el-option
                        v-for="item in stateDomainCdn"
                        :key="item.name"
                        :label="item.name"
                        :value="item.name">
                      </el-option>
                    </el-select>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>
    <el-dialog
      :title="addDialogTitle"
      :visible.sync="addDomainvisible">
      <div>
        <el-input class="large-input" size="large" v-model="addDomainName" placeholder="新增域名" @blur="domainName = domainName.trim()"></el-input>
      </div>
      <div v-if="addDomainInfo.length!=0"  v-loading.body="addDialogLoading">
        <el-table
          class="small-table"
          :data="addDomainInfo"
          border>
          <el-table-column prop="name"
                          label="属性"
                          align="center"
                          width="120px"/>
          <el-table-column prop="conf"
                          label="配置">
            <template slot-scope="scope">
              <div>
                <el-tag class="item-tag"
                  v-for="value in scope.row.conf"
                  key="key"
                  :closable="true"
                  :close-transition="true"
                  @close="handleDeleteConf(scope.$index, value)">
                  <span v-if="scope.row.name === 'CDN'">
                    {{value.name+':'+value.cname}}
                  </span>
                  <span v-else>
                    {{value}}
                  </span>
                </el-tag>
                <el-input class="large-input"
                  v-if="scope.row.showInput"
                  v-model="scope.row.inputValue"
                  size="small"
                  ref="saveTagInput"
                  placeholder="输入ip"
                  @keyup.enter.native="handleInputConfirm(scope.$index)"
                  @blur="scope.row.showInput = false"
                />
                <el-button v-else size="small" @click="handleShowInput(scope.$index)">
                  添加
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="handleCancelAdd">取消</el-button>
        <el-button type="primary" @click="addDomainSubmit">提交</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'SearchDomain',
    data () {
      return {
        addDomainvisible: false,
        addInputPlaceHolder: '',
        addDomainName: '',
        addDialogLoading: false,
        addDomainInfo: [],
        addDialogTitle: '域名新增',

        // View记录
        checkAllServerRooms: true,
        isSeverRoomsIndeterminate: false,
        checkedServerRooms: [],
        serverRooms: [],
        selectCdn: true,
        page: 1,
        pageSize: 15,
        domainName: '',
        domainListTotal: 0,
        domainList: [],
        domainListPage: [],
        loadingDomainList: false,

        checkAllIsps: true,
        isIspsIndeterminate: false,
        checkedIsps: [],
        isps: [],

        isMigrate: false,
        stateDomainName: '',
        stateDomainInfo: [],
        stateDomainCdn: [],
        domainOriginInfo: [],
        loadingDomainInfo: false,

        fullScreenLoading: false
      }
    },

    mounted () {
      this.fetchIsp()
      this.fetchServerRooms()
    },

    methods: {
      fetchIsp () {
        util.get(this, {
          url: '/web/view/list/isp',
          succ: (data) => {
            this.isps = data.data
            for (var i = 0; i < this.isps.length; i++) {
              this.checkedIsps.push(this.isps[i].name_in_english)
            }
          }
        })
      },

      fetchServerRooms () {
        util.get(this, {
          url: '/web/view/list/server_room',
          succ: (data) => {
            this.serverRooms = data.data
            this.checkedServerRooms = this.serverRooms
          }
        })
      },

      deleteDomain () {
        let domain = this.stateDomainName
        this.$confirm('是否删除该域名: ' + domain, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.fullScreenLoading = true
          util.post(this, {
            url: '/web/view/delete/view_domain',
            data: {domain_name: domain},
            succ: (data) => {
              util.notify(this, '成功', '删除域名成功')
              this.viewDomainList()
            }
          })
          this.fullScreenLoading = false
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除'
          })
        })
      },

      handleAddDomain () {
        this.addDialogTitle = '域名新增'
        this.addDomainvisible = true
        this.domainName = ''
        this.addDomainInfo = []
        // 构建新的DomainInfo
        for (var i = 0; i < this.serverRooms.length; i++) {
          let info = {name: this.serverRooms[i], inputValue: '', showInput: false, conf: []}
          this.addDomainInfo.push(info)
        }
        let cdn = {name: 'CDN', inputValue: '', showInput: false, conf: []}
        this.addDomainInfo.push(cdn)
      },

      handelEditDomain () {
        this.loadingDomainInfo = true
        util.get(this, {
          url: '/web/view/get/view_domain_info',
          data: {domain_name: this.stateDomainName},
          succ: (data) => {
            let rooms = data.data.rooms
            let cdns = data.data.cnames
            // 组装数据
            this.addDomainInfo = []
            this.addDialogTitle = '域名配置修改'
            this.addDomainName = this.stateDomainName
            // 机房状态
            for (let room of this.serverRooms) {
              let info = {name: room, inputValue: '', showInput: false, conf: []}
              if (room in rooms) {
                info.conf = rooms[room].ips
              }
              this.addDomainInfo.push(info)
            }
            let cdn = {name: 'CDN', inputValue: '', showInput: false, conf: cdns.cdn}
            this.addDomainInfo.push(cdn)
            this.addDomainvisible = true
          }
        })
        this.loadingDomainInfo = false
      },

      handleInputConfirm (index) {
        let inputValue = this.addDomainInfo[index].inputValue.trim()
        let name = this.addDomainInfo[index].name
        if (name === 'CDN') {
          inputValue = inputValue.split(':')
          if (inputValue.length === 2) {
            let name = inputValue[0].trim()
            let cname = inputValue[1].trim()
            if (cname === '' || name === '') {
              this.$message.warning('参数不能为空')
              return false
            }
            if (!util.isValidDomain(cname)) {
              this.$message.warning('CDN格式错误')
              return false
            }
            this.addDomainInfo[index].conf.push({name: inputValue[0].trim(), cname: inputValue[1].trim()})
          } else {
            this.$message.warning('请按照 name:cname的格式输入')
          }
        } else {
          if (inputValue && !util.isValidIP(inputValue)) {
            this.$message.warning('输入ip格式不正确')
            return false
          }
          if (inputValue) {
            this.addDomainInfo[index].conf.push(inputValue)
          }
        }
        this.addDomainInfo[index].showInput = false
        this.addDomainInfo[index].inputValue = ''
      },

      handleShowInput (index) {
        this.addDomainInfo[index].showInput = true
        let name = this.addDomainInfo[index].name
        this.$nextTick(_ => {
          this.$refs.saveTagInput.$refs.input.focus()
        })
        if (name === 'CDN') {
          this.addInputPlaceHolder = '输入CDN域名'
        } else {
          this.addInputPlaceHolder = '输入ip'
        }
      },

      handleCancelAdd () {
        this.addDialogTitle = ''
        this.addDomainvisible = false
        this.domainName = ''
        this.addDomainInfo = []
        this.viewDomainList()
      },

      handleDeleteConf (index, value) {
        let conf = this.addDomainInfo[index].conf
        conf.splice(conf.indexOf(value), 1)
      },

      addDomainSubmit () {
        if (this.addDomainName === '') {
          this.$message.warning('域名不能为空')
          return false
        }
        let submitArg = {
          domain_name: this.addDomainName
        }
        let rooms = {}
        let cnames = {}
        // 拼接提交参数
        for (let i = 0; i < this.addDomainInfo.length; i++) {
          let item = this.addDomainInfo[i]
          if (item.name !== 'CDN' && item.conf.length > 0) {
            rooms[item.name] = item.conf
          } else if (item.name === 'CDN' && item.conf.length > 0) {
            for (let element of item.conf) {
              cnames[element.name] = element.cname
            }
            submitArg['cnames'] = cnames
          }
        }

        if (JSON.stringify(rooms) === '{}' && JSON.stringify(cnames) === '{}') {
          this.$message.warning('请输入机房或CDN配置')
          return false
        }
        if (JSON.stringify(rooms) !== '{}') {
          submitArg['rooms'] = rooms
        }

        let confirmMsg = '是否新增域名'
        let url = '/web/view/add/view_domain'
        if (this.addDialogTitle !== '域名新增') {
          confirmMsg = '是否提交修改'
          url = '/web/view/update/view_domain'
        }
        this.$confirm(confirmMsg, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.addDialogLoading = true
          util.post(this, {
            url: url,
            data: submitArg,
            succ: (data) => {
              util.notify(this, '成功', '提交成功')
              this.addDomainvisible = false
              this.viewDomain(this.addDomainName)
            }
          })
          this.addDialogLoading = false
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消新增域名'
          })
        })
      },

      viewDomainList () {
        this.stateDomainName = ''
        this.loadingDomainList = true
        util.post(this, {
          url: '/web/view/list/view_domain',
          data: {
            server_rooms: this.checkedServerRooms,
            isps: this.checkedIsps,
            domain_name: this.domainName,
            select_cdn: this.selectCdn
          },
          succ: (data) => {
            this.page = 1
            this.domainList = data.data
            this.domainListTotal = this.domainList.length
            this.domainListPage = this.domainList.slice((this.page - 1) * this.pageSize, this.pageSize)
            this.loadingDomainList = false
            if (this.domainListTotal === 0) {
              this.$message.warning('无相关域名信息,请检查输入')
            } else {
              this.viewDomain(this.domainList[0].domain)
            }
          }
        })
        this.loadingDomainList = false
      },

      viewDomain (domainName) {
        console.log(domainName)
        this.loadingDomainInfo = true
        util.get(this, {
          url: '/web/view/get/view_domain_info',
          data: {domain_name: domainName},
          succ: (data) => {
            // 组装数据
            this.isMigrate = data.data.is_migrate
            this.stateDomainInfo = []
            // 机房状态
            let rooms = data.data.rooms
            for (let room in rooms) {
              let roomInfo = rooms[room]
              let info = {info: {name: room, is_enabled: roomInfo.is_enabled}}
              for (let isp in roomInfo.isps) {
                info[isp] = {is_enabled: roomInfo.isps[isp], ips: roomInfo.ips}
              }
              this.stateDomainInfo.push(info)
            }
            this.stateDomainInfo.sort(this.sortDomainInfo)
            // cdn
            let cdns = data.data.cnames
            this.stateDomainCdn = cdns.cdn
            this.stateDomainCdn.push({name: '不使用cdn', cname: '不使用cdn'})
            let cdn = {info: {name: 'cdn'}}
            let cdnIsps = cdns.isps
            for (let item in cdnIsps) {
              cdn[item] = cdnIsps[item]
            }
            this.stateDomainInfo.push(cdn)
            this.stateDomainName = data.data.domain_name

            // 记录最一开始的原始信息
            this.domainOriginInfo = this.deepCopy(this.stateDomainInfo)
            this.loadingDomainInfo = false
          }
        })
        this.loadingDomainInfo = false
      },

      switchAll (index, state) {
        for (var attr in this.stateDomainInfo[index]) {
          if (attr !== 'info') {
            this.stateDomainInfo[index][attr].is_enabled = state
            this.switchCn(attr, state)
          }
        }
      },

      switchCn (property, state) {
        if (state) {
          for (let i = 0; i < this.stateDomainInfo.length; i++) {
            let item = this.stateDomainInfo[i]
            if (item.info.name === 'cdn') {
              item[property].name = '不使用cdn'
              item[property].cname = '不使用cdn'
            }
          }
        }
      },

      switchCdn (property, key) {
        if (key !== '不使用cdn') {
          for (let item of this.stateDomainInfo) {
            if (item.info.name === 'cdn') {
              // 修改对应的cnmae
              for (let cdn of this.stateDomainCdn) {
                if (cdn.name === item[property].name) {
                  item[property].cname = cdn.cname
                }
              }
            } else {
              item[property].is_enabled = false
            }
          }
        }
      },

      getChangeIsp () {
        let diffIsp = new Set()
        for (let item of this.isps) {
          let isp = item.name_in_english
          for (let j = 0; j < this.stateDomainInfo.length; j++) {
            let cur = this.stateDomainInfo[j]
            let prev = this.domainOriginInfo[j]
            if (cur.info.name !== 'cdn') {
              if (cur[isp].is_enabled !== prev[isp].is_enabled) {
                diffIsp.add(isp)
              }
            }
            if (cur.info.name === 'cdn') {
              if (cur[isp].name !== prev[isp].name &&
                cur[isp].name !== '不使用cdn') {
                diffIsp.add(isp + ':cdn' + ':' + cur[isp].cname)
                diffIsp.delete(isp)
              }
            }
          }
        }
        return diffIsp
      },

      submitModify () {
        // 得到改变的isp
        let diffIsp = this.getChangeIsp()
        // 没有修改
        if (diffIsp.size === 0) {
          this.$message.warning('无修改,请勿提交.')
          return false
        }
        let submitArgs = {
          domain_name: this.stateDomainName
        }
        // 提取出修改的内容
        if (diffIsp.size !== 0) {
          let diffContent = {}
          for (let isp of diffIsp) {
            if (isp.indexOf(':') > 0) {
              let list = isp.split(':')
              diffContent[list[0]] = {cdn: list[2]}
            } else {
              // 普通机房状态修改
              // 遍历所有机房添加当前状态
              let rooms = []
              for (let i = 0; i < this.stateDomainInfo.length; i++) {
                let room = this.stateDomainInfo[i]
                if (room.info.name !== 'cdn') {
                  if (room[isp].is_enabled) {
                    rooms.push(room.info.name)
                  }
                }
              }
              diffContent[isp] = {rooms: rooms}
            }
          }
          submitArgs.isps = diffContent
          console.log(diffContent)
        }
        this.$confirm('是否提交修改', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.fullScreenLoading = true
          util.post(this, {
            url: '/web/view/update/view_domain_state',
            data: submitArgs,
            succ: (data) => {
              util.notify(this, '修改成功', '提交修改成功')
              this.fullScreenLoading = false
              this.viewDomain(this.stateDomainName)
            }
          })
          this.fullScreenLoading = false
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消提交'
          })
        })
      },

      handleCheckAllServerRoomChange (val) {
        this.checkedServerRooms = val ? this.serverRooms : []
        this.isSeverRoomsIndeterminate = false
        this.selectCdn = val
      },

      handleCheckedRoomsChange (value) {
        let checkedCount = value.length
        this.checkAllServerRooms = checkedCount === this.serverRooms.length
        this.isSeverRoomsIndeterminate = checkedCount > 0 && checkedCount < this.serverRooms.length
      },

      handleCheckAllIspsChange (val) {
        this.checkedIsps = []
        if (val) {
          for (var i = 0; i < this.isps.length; i++) {
            this.checkedIsps.push(this.isps[i].name_in_english)
          }
        }
        this.isIspsIndeterminate = false
      },

      handleCheckedIspsChange (value) {
        let checkedCount = value.length
        this.checkAllIsps = checkedCount === this.isps.length
        this.isIspsIndeterminate = checkedCount > 0 && checkedCount < this.isps.length
      },

      handleCurrentChange (val) {
        this.page = val
        this.domainListPage = this.domainList.slice((this.page - 1) * this.pageSize, val * this.pageSize)
      },

      deepCopy (source) {
        let result = {}
        for (let key in source) {
          result[key] = typeof (source[key]) === 'object' ? this.deepCopy(source[key]) : source[key]
        }
        return result
      },

      tagKey (name, value) {
        if (name === 'CDN') {
          return value.name
        } else {
          return value
        }
      },

      sortDomainInfo (a, b) {
        return a.info.name > b.info.name
      }
    }
  }
</script>

<style scoped>
  .option-div {
    margin-top: 10px;
  }

  .option-title {
    color: #428bca;
  }

  .option-item {
    margin-left: 20px;
  }

  .option-item-text {
    margin-left: 10px;
    font-size: 18px;
  }

</style>
