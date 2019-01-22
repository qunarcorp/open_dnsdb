import Vue from 'vue'
import Router from 'vue-router'
import Conf from '@/components/conf/Conf'
import HostManager from '@/components/conf/HostManager'
import ZoneManager from '@/components/conf/ZoneManager'
import View from '@/components/view/View'
import Record from '@/components/record/Record'
import DnsLog from '@/components/log/DnsLog'
import Preview from '@/components/preview/Preview'
import Login from '@/components/admin/Login'
import System from '@/components/system/System'
import UserManager from '@/components/system/UserManager'
import Menu from '@/components/Menu'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'approot',
      component: Menu,
      children: [
        {
          path: 'system',
          component: System,
          children: [
            {
              path: 'user',
              component: UserManager
            }
          ]
        },
        {
          path: 'preview',
          name: 'preview',
          component: Preview
        },
        {
          path: 'view',
          name: 'view',
          component: View
        },
        {
          path: 'record',
          name: 'Record',
          component: Record
        },
        {
          path: 'conf',
          name: 'Conf',
          component: Conf,
          children: [
            {
              path: 'zone',
              component: ZoneManager
            },
            {
              path: 'hostgroup',
              component: HostManager
            }
          ]
        },
        {
          path: 'dnslog',
          name: 'DnsLog',
          component: DnsLog
        }
      ]
    }
  ]
})
