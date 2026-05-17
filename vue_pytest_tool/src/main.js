import babelpolyfill from 'babel-polyfill'
import Vue from 'vue'
import App from './App'
import ElementUI from 'element-ui'
import { Message } from 'element-ui'
// import 'element-ui/lib/theme-chalk/index.css'
// import 'element-ui/lib/theme-default/index.css'
// import '//unpkg.com/element-ui@2.13.2/lib/theme-chalk/index.css'
// import './assets/theme/theme-#006a63/index.css'
// import './assets/theme/theme-darkblue/index.css'
// import './assets/theme/theme-green/index.css'
import './assets/theme/theme-213/index.css'
import VueRouter from 'vue-router'
import store from './vuex/store'
import Vuex from 'vuex'
import routes from './routes'
import elCascaderMulti from "el-cascader-multi";
import 'font-awesome/css/font-awesome.min.css'
import axios from 'axios';

Vue.use(ElementUI)
Vue.use(VueRouter)
Vue.use(Vuex)
Vue.use(elCascaderMulti)

const router = new VueRouter({
  routes
})

let authExpiredNotified = false;

// http request 拦截器
axios.interceptors.request.use(
  config => {
    var token = sessionStorage.getItem('token');
    if (token) {  // 判断是否存在token，如果存在的话，则每个http header都加上token
      token =sessionStorage.getItem('token')+':';
      config.headers.Authorization = `Basic ${new Buffer(token).toString('base64')}`;
    }
    return config;
  },
  error => {
    Message({
      message: "登录状态信息过期,请重新登录",
      type: "error"
    });
    router.push({
      path: "/login"
    });
    return Promise.reject(error);
  });

// http response 拦截器

axios.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 返回 401 清除token信息并跳转到登录页面
          sessionStorage.removeItem('token');
          sessionStorage.removeItem('user');
          sessionStorage.removeItem('username');
          localStorage.removeItem('token');
          if (router.currentRoute.path !== "/login") {
            router.replace({
              path: "/login"
            });
          }
          if (!authExpiredNotified) {
            authExpiredNotified = true;
            Message({
              message: '登录状态已失效，请重新登录',
              type: 'error'
            });
            setTimeout(() => {
              authExpiredNotified = false;
            }, 3000);
          }
          break;
      }
    }
    return Promise.reject(error);
  });
// router.beforeEach((to, from, next) => {
//   if (to.path == '/login') {
//     sessionStorage.removeItem('token');
//   }
//   let token = sessionStorage.getItem('token');
//   if (!token && to.path != '/login') {
//     next({ path: '/login' })
//   } else {
//     next()
//   }
// })

var app=new Vue({
  //el: '#app',
  //template: '<App/>',
  router,
  store,
  //components: { App }
  render: h => h(App)
}).$mount('#app')


