<template>
  <div id="app">
    <!-- 头部导航 -->
    <header>
      <div>
        <div class="title">
          <i class="fa fa-cloud"/>
          <span>DNSDB</span>
        </div>
        <div class="user">
          <i class="fa fa-user"/>
          <span>{{userName}}</span>
          <span style="color: white;margin-left: 10px;cursor: pointer" @click="logout">注销</span>
        </div>
      </div>
    </header>
    <body>
      <router-view></router-view>
    </body>
  </div>
</template>


<script>
  import { mapState } from 'vuex'
  import utils from '@/common/util'
  import Login from '@/components/admin/Login'
  import Menu from '@/components/Menu'
  export default {
    name: 'app',
    mounted () {
      this.getUser()
    },

    components: { Login, Menu },

    computed: mapState({
      userName: state => state.userName
    }),

    methods: {
      getUser () {
        utils.get(this, {
          url: '/web/auth/logged_in_user',
          succ: (data) => {
            this.$store.commit('changeUsername', data.data)
            // this.$router.push('/')
          }
        })
      },

      logout () {
        this.$store.commit('changeUsername', '')
        utils.post(this, {
          url: '/web/auth/logout',
          succ: (data) => {
            console.log(data)
          }
        })
      }
    }
  }
</script>
<style>
  #app {
    min-width: 100%;
    height: 100%;
    margin: 0 auto;
    background: #eef1f6;
    font-family: "Helvetica Neue",Helvetica,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","微软雅黑",Arial,sans-serif;
  }

  /* 头部导航 */
  header {
    z-index: 1000;
    transition: all 0.5s ease;
    background-color: #337ab7;
    box-shadow: 0 2px 4px 0 rgba(0, 0, 0, .12), 0 0 6px 0 rgba(0, 0, 0, .04);
    padding-bottom: 3px;
    padding-top: 3px;
  }

  header .title {
    display: inline-block;
    color: white;
    font-size: 24px;
    margin-top: 14px;
    margin-bottom: 14px;
    margin-left: 20px;
  }

  header .user {
    display: inline-block;
    color: white;
    font-size: 18px;
    margin-top: 16px;
    margin-right: 20px;
    float: right;
  }

  .navbar {
    background: #eef1f6;
    height: 100%;
  }

  body {
    margin: 0;
    background: white;
    height: 93%;
  }

  .ferrorhead3 {
    width: 298px;
    margin-top: -3px;
    color: #fa5b5b;
    font-size: 12px;
    line-height: 20px;
    vertical-align: top;
    word-break: break-all;
  }

</style>
