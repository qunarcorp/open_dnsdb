<template>
  <div class="preview">

    <div class="preview-panel">
      <span class="title">已迁移机房:</span>
      <span class="title" v-if="migrateHistory.length===0">无</span>
      <div class="tab-panel" v-if="migrateHistory.length > 0">
        <el-table
          class="medium-table"
          border
          :data="migrateHistory">
          <el-table-column 
            prop="migrate_rooms"
            label="迁移机房"
            align="center"/>
          <el-table-column 
            prop="migrate_isps"
            label="迁移运营商"
            align="center">   
          </el-table-column>
          <el-table-column
            prop="dst_rooms"
            label="目标机房"
            align="center">
          </el-table-column>
        </el-table>
      </div>
    </div>
    <hr/>
    <!-- <div class="preview-panel">
      <span class="title">已切换IP:</span>
      <span class="title" v-if="switchHistory.length===0">无</span>
      <div style="margin-top: 5px" v-for="history in switchHistory">
        <span style="font-size: 18px">IP:</span>
        <span style="font-size: 18px">{{history[0]}}</span>
        <span style="font-size: 18px;margin-left: 20px">切换类型:</span>
        <span style="font-size: 18px" v-if="history[1]=='replace'">IP替换</span>
        <span style="font-size: 18px" v-if="history[1]=='aqb'">切换高防</span>
      </div>
    </div>
    <hr/> -->
    <div class="preview-panel">
      <span class="title">已迁移ACL:</span>
      <span class="title" v-if="aclMigrateHistory.length===0">无</span>
      <div class="tab-panel" v-if="aclMigrateHistory.length > 0">
        <el-table
          class="medium-table"
          border
          :data="aclMigrateHistory">
          <el-table-column 
            prop="subnet"
            label="网段"
            align="center"/>
          <el-table-column
            label="所属运营商"
            align="center">
            <template slot-scope="scope">
              <span class="demonstration"> {{ viewIspDict[scope.row.origin_acl] }} </span>
            </template>        
          </el-table-column>
          <el-table-column
            label="当前运营商"
            align="center">
            <template slot-scope="scope">
              <span class="demonstration"> {{ viewIspDict[scope.row.now_acl] }} </span>
            </template>  
          </el-table-column>
        </el-table>
      </div>
    </div>
    <hr/>
    <div class="preview-panel">
      <span class="title">域名统计</span>
      <div class="tab-panel" v-if="domainCount.length > 0">
        <el-table
          class="medium-table"
          border
          :data="domainCount">
          <el-table-column 
            prop="zone"
            label="Zone"/>
          <el-table-column 
            prop="count"
            label="域名数"
            align="center">   
          </el-table-column>
        </el-table>
      </div>
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
        domainCount: 0,
        migrateHistory: [],
        switchHistory: [],
        aclMigrateHistory: [],
        viewIspDict: {}
      }
    },
    mounted () {
      this.fetchDnsViewPriview()
      this.fetchViewIspInfo()
    },
    methods: {
      fetchDnsViewPriview () {
        util.get(this, {
          url: domain + 'get/previewinfo',
          succ: (data) => {
            this.domainCount = data.data.domain_count
            console.log(this.domainCount)
            this.domainCount.sort((a, b) => {
              return a.count - b.count
            })
            this.migrateHistory = data.data.migrate
            this.switchHistory = data.data.switch
            this.aclMigrateHistory = data.data.acl_migrate
          }
        })
      },

      fetchViewIspInfo () {
        util.get(this, {
          url: '/web/view/list/acl_isp_info',
          succ: (data) => {
            this.viewIspDict = data.data
          }
        })
      }
    }
  }
</script>

<style scoped>
  hr {
    border-top: 1px;
    margin-top: 20px;
  }

  .preview {
    background: white;
    height: 100%;
  }
  .preview-panel {
    padding-top: 20px;
    padding-left: 20px;
  }

  .title {
    display: inline-block;
    width: 180px;
    font-size: 22px;
    color: steelblue;
  }

  .medium-table {
    width: 500px;
    font-size:16px;
  }
</style>
