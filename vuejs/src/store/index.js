import { createStore } from 'vuex'
import main from './main'
import topMenu from './top-menu'
import meters from './modules/meters'
import readings from './modules/readings'
import alerts from './modules/alerts'
import users from './modules/users'

const store = createStore({
  modules: {
    main,
    topMenu,
    meters,
    readings,
    alerts,
    users
  }
})

export function useStore() {
  return store
}

export default store