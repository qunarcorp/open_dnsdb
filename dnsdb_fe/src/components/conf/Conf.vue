<template>
  <body>
    <div>
      <el-tabs v-model="activeName" type="card">
        <el-tab-pane class="tab-panel" label="主机管理" name="host">
          <HostManager/>
        </el-tab-pane>
        <el-tab-pane class="tab-panel" label="Zone管理" name="zone">
          <ZoneManager/>
        </el-tab-pane>
        <el-tab-pane class="tab-panel" label="Header编辑" name="header">
          <HeaderEdit/>
        </el-tab-pane>
        <!-- <el-tab-pane class="tab-panel" label="ACL管理" name="acl">
          <AclManager/>
        </el-tab-pane>
        <el-tab-pane class="tab-panel" label="部署历史" name="deploy">
          <DeployHistory/>
        </el-tab-pane> -->
      </el-tabs>
    </div>
  </body>
</template>

<script>
  import ZoneManager from '@/components/conf/ZoneManager'
  import HostManager from '@/components/conf/HostManager'
  import HeaderEdit from '@/components/conf/HeaderEdit'

  export default {
    name: 'Manager',
    components: {
      ZoneManager: ZoneManager,
      HostManager: HostManager,
      HeaderEdit: HeaderEdit
    },
    data () {
      return {
        activeName: 'host'
      }
    }
  }
</script>


<style scoped>

</style>
