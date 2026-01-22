import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import globalComponents from './global-components'
import utils from './utils'
import './libs'
import Multiselect from '@vueform/multiselect'
import './assets/sass/app.scss'
import axios from 'axios'

axios.defaults.baseURL = import.meta.env.VITE_APP_API_BASE_URL
axios.defaults.timeout = 60000

const token = localStorage.getItem('token')
if (token) {
  axios.defaults.headers.common['Authorization'] = `JWT ${token}`
}

const app = createApp(App)
  .use(store)
  .use(router)

globalComponents(app)
utils(app)

app.component('Multiselect', Multiselect)

app.mount('#app')