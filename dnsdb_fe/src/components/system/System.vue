<template>
  <div>
    <el-tabs v-model="activeName" type="card">
      <el-tab-pane name="user" label="用户管理">
        <UserManager/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
  import UserManager from '@/components/system/UserManager'
  export default {
    name: 'System',
    components: {
      UserManager: UserManager
    },
    data () {
      return {
        activeName: 'user'
      }
    }
  }
</script>

<style scoped>

</style>
