import Vue from 'vue'
import Router from 'vue-router'
import PingPongMain from '@/components/PingPongMain'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'PingPongMain',
      component: PingPongMain
    }
  ]
})
