<template>
  <div class="login-div-container">
    <div  class="login-div">
      <div class="login-title" >登录</div>
      <el-form ref="form" label-position="top" :model="form" label-width="80px" :rules="rules">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="form.password"></el-input>
        </el-form-item>
        <el-form-item>
          <div class="login-button-div">
            <el-button class="login-button" type="primary" @click="onSubmit">登录</el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
 import { mapState } from 'vuex'
 import util from '@/common/util.js'
 export default {
   name: 'page',
   mounted () {
     this.$store.commit('changeUsername', '')
   },
   data () {
     return {
       errMsg: '',
       form: {
         username: '',
         password: ''
       },

       rules: {
         username: [
           { required: true, message: '请输入用户名', trigger: 'blur' },
           { min: 4, max: 64, message: '长度在 4 到 64 个字符', trigger: 'blur' }
         ],
         password: [
           { required: true, message: '请输入密码', trigger: 'blur' },
           { min: 6, max: 9, message: '长度在 6 到 9 个字符', trigger: 'blur' }
         ]
       }
     }
   },
   methods: {
     onSubmit (e) {
       this.$refs['form'].validate((valid) => {
         if (valid) {
           util.post(this, {
             url: '/web/auth/login',
             data: {
               'username': this.form.username,
               'password': this.form.password
             },
             post_data_type: 'json',
             succ: (data) => {
               this.resetForm('form')
               this.$store.commit('changeUsername', data.data)
               console.log(this.$store.state.userName)
               this.goBack()
             }
           })
         } else {
           return false
         }
       })
     },

     resetForm (formName) {
       this.$refs[formName].resetFields()
     },

     goBack () {
       window.history.length > 1
         ? this.$router.go(-1)
         : this.$router.push('/')
     }
   },
   computed: {
     ...mapState({
       'loading': 'loading'
     })
   }
 }

</script>

<style scoped>
  .login-div-container {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .login-div {
    width: 450px;
    border: solid;
    padding: 75px;
    border-radius: 20px;
    border-width: 1px
  }

  .login-title {
    width: 100%;
    padding-bottom: 20px;
    text-align: center;
    font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
    font-size: 40px;
  }

  .validate-col {
    display: flex;
    justify-content: center;
    height: 40px;
  }

  .login-button-div {
    width: 100%;
    text-align: center;
    margin-bottom: -50px;
  }

  .login-button {
    width: 50%
  }
</style>
