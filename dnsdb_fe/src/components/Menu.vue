<template>
  <el-row  style="height: 100%">
    <el-col :xs="4" :sm="4" :md="3" :lg="2" style="height: 100%">
      <div class="navbar">
        <el-menu :default-active="activeIndex" @select="handleSelect">
          <el-menu-item index="1"><i style=" width: 24px;height: 16px;" class="fa fa-star" ></i>系统概览</el-menu-item>
          <el-menu-item index="2"><i style=" width: 24px;height: 16px;" class="fa fa-circle-o"></i>普通域名</el-menu-item>
          <el-menu-item index="3"><i style=" width: 24px;height: 16px;" class="fa fa-viacoin"></i>View域名</el-menu-item>
          <el-menu-item index="4"><i style=" width: 24px;height: 16px;" class="fa fa-map"></i>配置管理</el-menu-item>
          <el-menu-item index="5"><i style=" width: 24px;height: 16px;" class="fa fa-cog"></i>系统管理</el-menu-item>
          <el-menu-item index="6"><i style=" width: 24px;height: 16px;" class="fa fa-steam"></i>操作日志</el-menu-item>
        </el-menu>
      </div>
    </el-col>
    <el-col :xs="20" :sm="20" :md="21" :lg="22" style="height: 100%">
        <router-view></router-view>
    </el-col>
  </el-row>
</template>

<script>
  let tabIndex = {
    '1': '/preview',
    '2': '/record',
    '3': '/view',
    '4': '/conf',
    '5': '/system',
    '6': '/dnslog'
  }
  let revTabIndex = {}
  for (let i in tabIndex) {
    revTabIndex[tabIndex[i]] = i
  }
  export default {
    name: 'dnsdbmenu',
    data () {
      return {
        activeIndex: '1'
      }
    },

    mounted () {
      if (this.$router.currentRoute.path === '/') {
        this.$router.push('/preview')
      } else {
        this.activeIndex = revTabIndex[this.$router.currentRoute.path]
        this.$router.push(tabIndex[this.activeIndex])
      }
    },

    methods: {
      handleSelect (key) {
        this.activeIndex = key
        this.$router.push(tabIndex[this.activeIndex])
      }
    }
  }
</script>

<style>
</style>

