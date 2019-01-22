<template>
  <div>
    <el-row :gutter="0" type="flex"  >
      <el-col :span="3">
        <label class="large-title">Zone列表</label>
        <div class="list-div">
          <div v-for="item in zoneList" class="list-item" v-text="item" @click="getZoneHeader(item)">
            {{item}}
          </div>
        </div>
      </el-col>
      <el-col :span="21">
        <div class="tab-panel" v-if="curZoneName !==''">
          <el-row :gutter="0" type="flex" >
            <el-col :span="20">
              <div class="medium-title">
                <span >当前Zone：{{ curZoneName }}</span>
              </div>
            </el-col>
            <el-col :span="4" style="text-align: right">
              <el-button size="large" @click="checkZoneHeader">检查</el-button>
              <el-button size="large" type="warning" @click="updateZoneHeader">提交</el-button>
            </el-col>
          </el-row>
          <div>
            <el-input
              v-loading="updateHeaderLoading"
              v-if="zoneHeaderContent !== ''"
              style="margin-top: 10px"
              type="textarea"
              autosize
              spellcheck="false"
              placeholder="zone header"
              v-model="zoneHeaderContent">
            </el-input>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'HeaderEdit',
    data () {
      return {
        zoneList: [],
        curZoneName: '',
        zoneHeaderContent: '',
        updateHeaderLoading: false
      }
    },

    mounted () {
      this.fetchZoneList()
    },

    methods: {
      fetchZoneList () {
        util.get(this, {
          url: '/web/config/list/zone_header',
          succ: (data) => {
            this.zoneList = data.data
          }
        })
      },

      getZoneHeader (zone) {
        util.get(this, {
          url: '/web/config/get/zone_header',
          data: {zone_name: zone},
          succ: (data) => {
            this.curZoneName = zone
            this.zoneHeaderContent = data.data.header
          }
        })
      },

      checkZoneHeader () {
        util.post(this, {
          url: '/web/config/check_zone_header',
          data: {zone_name: this.curZoneName, header_content: this.zoneHeaderContent},
          succStr: '语法检查通过！'
        })
      },

      updateZoneHeader () {
        this.$confirm('是否更新' + this.curZoneName + '的头文件?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/config/update/zone_header',
            data: {zone_name: this.curZoneName, header_content: this.zoneHeaderContent},
            succ: (data) => {
              util.notify(this, '成功', '更新头文件成功')
              this.updateHeaderLoading = true
              this.getZoneHeader(this.curZoneName)
              this.updateHeaderLoading = false
            }
          })
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消更新头文件'
          })
        })
      }
    }
  }
</script>

<style scoped>
  .list-div {
    height: 750px;
    overflow: auto
  }
</style>
