<template>
  <div>
    <el-tabs v-model="activeTab" type="card">
      <el-tab-pane label="域名管理" name="domain">
        <DomainManager/>
      </el-tab-pane>
      <el-tab-pane label="迁移管理" name="migrate">
        <Migrate/>
      </el-tab-pane>
      <el-tab-pane label="运营商管理" name="isp">
        <IspManager/>
      </el-tab-pane>
      <el-tab-pane label="ACL管理" name="acl">
        <AclManager/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>


<script>
  import DomainManager from '@/components/view/DomainManager'
  import IpManager from '@/components/view/IpManager'
  import IspManager from '@/components/view/IspManager'
  import AclManager from '@/components/view/AclManager'
  import Migrate from '@/components/view/Migrate'

  export default {
    name: 'ViewIndex',
    components: {
      DomainManager: DomainManager,
      IpManager: IpManager,
      IspManager: IspManager,
      AclManager: AclManager,
      Migrate: Migrate
    },
    data () {
      return {
        activeTab: 'domain'
      }
    }
  }
</script>

<style scoped>

</style>
