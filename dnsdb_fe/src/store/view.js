import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    menu_index: '/system',
    loading: false,
    activeTab: 'user',
    userName: ''
  },
  mutations: {
    changeTab (state, tabName) {
      state.activeTab = tabName
      console.log(tabName)
    },
    changeMenuIndex (state, idx) {
      console.log(idx)
      state.menu_index = idx
    },
    changeUsername (state, username) {
      state.userName = username
    }
  }
})
