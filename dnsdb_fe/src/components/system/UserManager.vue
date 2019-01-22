<template>
  <div>
    <div class="tab-panel">
      <el-row>
        <el-col :span="12"><div class="grid-content">
          <el-select v-model="searchType" 
            clearable size='large' 
            placeholder="搜索类型">
            <el-option
              v-for="item in searchOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <el-select v-if="searchType === 'byRole'"
            v-model="searchRole" 
            clearable size='large' 
            @change="fetchUser"
            placeholder="请选择角色">
            <el-option
              v-for="item in roleOption"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <el-input v-if="searchType === 'byUser'"
            class="large-input" 
            size="large" 
            v-model="searchName" 
            placeholder="请输入用户名" 
            @keyup.enter.native="fetchUser"/>
          <el-button size="large" type="info" @click="fetchUser">搜索</el-button>
        </div></el-col>
        <el-col :span="12"><div class="grid-content">
          <el-button size="large" type="info" @click="addUserVisible = true">添加</el-button>
        </div></el-col>
      </el-row>
    </div>
    <hr/>
    <div class="tab-panel">
      <el-table
        :data="userList">
        <el-table-column prop="username"
                         label="用户名"
                         width="300px"
                         align="center"/>
        <el-table-column prop="email"
                         label="邮箱"
                         width="300px"
                         align="center">
        </el-table-column>
        <el-table-column prop="role"
                         label="角色"
                         width="300px"
                         align="center">
          <template slot-scope="scope">
            <span>{{ roleObj[scope.row.role_id] }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="opration"
                         label="操作"
                         width="300px"
                         align="center">
          <template slot-scope="scope">
            <el-button type="danger" size="small" @click="deleteUser(scope.row.username)">删除</el-button>
            <!-- <el-button type="primary" size="small" @click="updateUser(scope.row)">编辑</el-button> -->
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        align="right"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-size="pageSize"
        :total="total">
      </el-pagination>
    </div>
    <el-dialog
      title="添加用户"
      :visible.sync="addUserVisible"
      width="30%">
      <el-form status-icon :model="addUserForm" :rules="addUserRules" ref="addUserForm" label-position="left" label-width="120px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addUserForm.username" @blur="addUserForm.username = addUserForm.username.trim()"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="addUserForm.email" @blur="addUserForm.email = addUserForm.email.trim()"></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="roleId">
          <el-select
            v-model="addUserForm.roleId" 
            clearable size='large' 
            placeholder="请选择角色">
            <el-option
              v-for="item in roleOption"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addUserForm.password" type="password"></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="addUserForm.confirmPassword" type="password"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="addUserVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitForm('addUserForm')">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
  import util from '@/common/util.js'
  export default {
    name: 'UserManager',
    data () {
      var validatePass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请输入密码'))
        } else {
          if (this.addUserForm.confirmPassword !== '') {
            this.$refs.addUserForm.validateField('confirmPassword')
          }
          callback()
        }
      }

      var validateConfirmPass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请再次输入密码'))
        } else if (value !== this.addUserForm.password) {
          callback(new Error('两次输入密码不一致!'))
        } else {
          callback()
        }
      }
      return {
        roleObj: [],

        roleOption: [],
        searchOptions: [{
          label: '用户名',
          value: 'byUser'
        }, {
          label: '角色',
          value: 'byRole'
        }],
        searchType: 'byRole',
        searchRole: '',
        searchName: '',
        userList: [],
        page: 1,
        pageSize: 10,
        total: 0,

        addUserForm: {
          username: '',
          email: '',
          roleId: '',
          password: '',
          confirmPassword: ''
        },

        addUserRules: {
          username: [
            { required: true, message: '请输入用户名', trigger: 'blur' },
            { min: 4, max: 64, message: '长度在 4 到 64 个字符', trigger: 'blur' }
          ],
          email: [
            { required: true, message: '请输入邮箱', trigger: 'blur' }
          ],
          roleId: [
            { required: true, message: '请选择用户角色', trigger: 'change' }
          ],
          password: [
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 6, max: 9, message: '长度在 6 到 9 个字符', trigger: 'blur' },
            { validator: validatePass, trigger: 'blur' }
          ],
          confirmPassword: [
            { validator: validateConfirmPass, trigger: 'blur' },
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 6, max: 9, message: '长度在 6 到 9 个字符', trigger: 'blur' }
          ]
        },
        addUserVisible: false
      }
    },

    mounted () {
      this.fetchRoleObj()
      this.fetchUser()
    },

    methods: {
      fetchRoleObj () {
        util.get(this, {
          url: '/web/user/roles',
          succ: (data) => {
            this.roleObj = data.data
            this.roleOption = util.objToOptions(this.roleObj)
          }
        })
      },

      fetchUserByUser () {
        this.page = 1
        util.strTrim(this, 'searchName')
        util.get(this, {
          url: '/web/user/get',
          data: {username: this.searchName},
          succ: (data) => {
            this.userList = data.data
          }
        })
      },

      fetchUserByRole () {
        let params = {
          page: this.page,
          page_size: this.pageSize
        }
        if (this.searchRole !== '') {
          params['role_id'] = this.searchRole
        }
        util.get(this, {
          url: '/web/user/list',
          data: params,
          succ: (data) => {
            this.userList = data.data
          }
        })
      },

      fetchUser () {
        if (this.searchType === 'byUser') {
          return this.fetchUserByUser()
        } else {
          return this.fetchUserByRole()
        }
      },

      handleCurrentChange (val) {
        this.page = val
        this.fetchUser()
      },

      submitForm (formName) {
        this.$refs[formName].validate((valid) => {
          if (valid) {
            this.addUser()
          } else {
            return false
          }
        })
      },

      addUser () {
        util.post(this, {
          url: '/web/user/add',
          data: {username: this.addUserForm.username, email: this.addUserForm.email, password: this.addUserForm.password, role_id: this.addUserForm.roleId},
          succ: (data) => {
            this.addUserVisible = false
            util.notify(this, '成功', '用户添加成功')
            this.fetchUser()
          }
        })
      },

      postUserDelete (data) {
        util.post(this, {
          url: '/web/user/delete',
          data: data,
          succ: (data) => {
            util.notify(this, '成功', '删除用户成功')
            this.fetchUser()
          }
        })
      },

      deleteUser (username) {
        util.confirm(this, '是否删除用户' + username + '?', this.postUserDelete, {username: username})
      }
    }
  }
</script>

<style scoped>
  .list-div {
    width: 200px;
    display: inline-block;
  }
</style>
