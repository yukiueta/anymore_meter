const state = () => {
  return {
    menu: [
      {
        icon: 'AirplayIcon',
        pageName: 'dashboard',
        title: 'ダッシュボード',
        category: 'dashboard'
      }
    ]
  }
}

// getters
const getters = {
  menu: state => state.menu
}

// actions
const actions = {}

// mutations
const mutations = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
