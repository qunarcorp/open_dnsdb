<template>
  <div>
    <el-tabs v-model="activeName" type="card" @tab-click="handleTabClick">
      <el-tab-pane label="域名管理" name="record">
        <RecordManager/>
      </el-tab-pane>
      <el-tab-pane label="子网管理" name="subnet">
        <SubnetManager/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
  import RecordManager from '@/components/record/RecordManager'
  import SubnetManager from '@/components/record/SubnetManager'

  export default {
    name: 'Record',
    components: {
      RecordManager: RecordManager,
      SubnetManager: SubnetManager
    },
    data () {
      return {
        activeName: 'record'
      }
    },
    mounted () {
    },
    methods: {
      handleTabClick (tab, event) {
        if (tab.$data.index === '1') {

        } else {
          this.domainInfo = []
        }
      }
    }
  }
</script>

<style scoped>

</style>
