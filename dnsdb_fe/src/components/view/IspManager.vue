<template>
  <div>
    <div class="tab-panel">
      <el-table :data="editIspArray.data" border style="width: 100%" highlight-current-row>
        <el-table-column label="运营商" align="center">
          <el-table-column v-for="v in editIspArray.columns" :key="v.field" :prop="v.field" :label="v.title">
              <template slot-scope="scope">
                  <span v-if="scope.row.isSet">
                      <el-input size="medium" v-model="editIspArray.sel[v.field]">
                      </el-input>
                  </span>
                  <span v-else>{{scope.row[v.field]}}</span>
              </template>
          </el-table-column>
          <el-table-column label="操作">
              <template slot-scope="scope">
                  <span v-if="scope.row.isSet" class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="submitIsp(scope.row,scope.$index)">
                    提交
                  </span>
                  <span v-if="scope.row.isSet" class="el-tag el-tag--info el-tag--medium" style="cursor: pointer;" @click="handleCancelIsp(scope.row,scope.$index)">
                    取消
                  </span>
                  <span v-if="!scope.row.isSet" class="el-tag el-tag--danger el-tag--medium" style="cursor: pointer;" @click="submitDeleteIsp(scope.row.name_in_english, scope.$index)">
                    删除
                  </span>
                  <!-- <span v-if="!scope.row.isSet" class="el-tag el-tag--danger el-tag--medium" style="cursor: pointer;" @click="handleEditIsp(scope.row, scope.$index)">
                    编辑
                  </span> -->
              </template>
          </el-table-column>
        </el-table-column>
      </el-table>
      <div class="el-table-add-row" style="width: 100%;" @click="handleAddIsp"><span>+ 添加</span></div>
    </div>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'IspManager',
    data () {
      return {
        isps: [],
        ispEname: '',
        ispCname: '',
        ispAname: '',
        editIspArray: {
          sel: null, // 选中行
          editType: 'add',
          checkFileds: ['name_in_english', 'name_in_chinese', 'abbreviation'],
          addFileds: ['name_in_english', 'name_in_chinese', 'abbreviation', 'acl_name', 'acl_file'],
          columns: [
            { field: 'name_in_english', title: '英文名' },
            { field: 'name_in_chinese', title: '中文别名' },
            { field: 'abbreviation', title: '英文简写' },
            { field: 'acl_name', title: 'ACL名称' },
            { field: 'acl_file', title: 'ACL文件' }
          ],
          data: []
        }
      }
    },

    mounted () {
      this.fetchIsp()
    },

    methods: {
      fetchIsp () {
        util.get(this, {
          url: '/web/view/list/isp',
          succ: (data) => {
            this.editIspArray.data = data.data
            this.isps = data.data
          }
        })
      },

      checkSubmit () {
        for (let index in this.editIspArray.data) {
          let row = this.editIspArray.data[index]
          if (row.isSet) {
            this.$message.warning('请先提交当前编辑项')
            return false
          }
        }
        return true
      },

      handleAddIsp () {
        if (!this.checkSubmit()) {
          return false
        }
        let j = { name_in_english: '', abbreviation: '', name_in_chinese: '', acl_name: '', acl_file: '', isSet: true }
        this.editIspArray.data.push(j)
        this.editIspArray.sel = JSON.parse(JSON.stringify(j))
        this.editIspArray.editType = 'add'
      },

      handleCancelIsp (row, index) {
        if (this.editIspArray.editType === 'add') {
          this.editIspArray.data.splice(index, 1)
        } else {
          this.fetchIsp()
          this.editIspArray.sel = {}
        }
      },

      handleEditIsp (row, index) {
        if (!this.checkSubmit()) {
          return false
        }
        this.editIspArray.editType = 'update'
        row.isSet = true
        this.editIspArray.sel = JSON.parse(JSON.stringify(row))
      },

      addIsp (data) {
        this.$confirm('是否添加运营商', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/view/add/isp',
            data: data,
            succ: (data) => {
              util.notify(this, '成功', '添加运营商成功', 'success')
              this.editIspArray.sel = {}
              this.fetchIsp()
            }
          })
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '取消添加运营商',
            duration: 1500
          })
        })
      },

      updateIsp (row, data) {
        let param = {}
        for (let f of this.editIspArray.addFileds) {
          if (f !== 'name_in_english' && row[f] !== data[f]) {
            param[f] = data[f]
          }
        }
        this.$confirm('是否修改运营商信息', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          util.post(this, {
            url: '/web/view/update/isp',
            data: {name_in_english: data.name_in_english, update_data: param},
            succ: (data) => {
              util.notify(this, '成功', '修改运营商成功', 'success')
              row.isSet = false
              this.editIspArray.sel = {}
              this.fetchIsp()
            }
          })
        }).catch(() => {
          this.$notify.info({
            title: '取消',
            message: '取消添加运营商',
            duration: 1500
          })
        })
      },

      submitIsp (row, index) {
        let data = JSON.parse(JSON.stringify(this.editIspArray.sel))
        for (let f of this.editIspArray.addFileds) {
          data[f] = data[f].trim()
        }
        for (let f of this.editIspArray.checkFileds) {
          if (data[f] === '') {
            this.$message.warning('字段不能为空')
            return false
          }
        }
        if (this.editIspArray.editType === 'add') {
          this.addIsp(data)
        } else {
          this.updateIsp(row, data)
        }
      },

      submitDeleteIsp (ename, index) {
        for (let index in this.editIspArray.data) {
          let row = this.editIspArray.data[index]
          if (row.isSet) {
            this.$message.warning('请先提交当前编辑项')
            return false
          }
        }
        this.$confirm('确认删除主机 ' + ename, '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
          .then(() => {
            util.post(this, {
              url: 'web/view/delete/isp',
              data: {name_in_english: ename},
              succ: (data) => {
                util.notify(this, '成功', '删除运营商成功')
                this.fetchIsp()
              }
            })
          })
          .catch(() => {})
      }
    }
  }
</script>

<style scoped>


</style>
