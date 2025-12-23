const state = () => {
  return {
    menu: [
      {
        icon: 'AirplayIcon',
        pageName: 'dashboard',
        title: 'ダッシュボード',
        category: 'dashboard'
      },
      {
        icon: 'CpuIcon',
        pageName: 'meter-list',
        title: 'メーター',
        category: 'meters'
      },
      {
        icon: 'BarChart2Icon',
        pageName: 'reading-list',
        title: 'データ',
        category: 'readings'
      },
      {
        icon: 'AlertTriangleIcon',
        pageName: 'alert-list',
        title: 'アラート',
        category: 'alerts'
      },
      {
        icon: 'UsersIcon',
        pageName: 'user-list',
        title: 'ユーザー',
        category: 'settings'
      }
    ]
  }
}

const getters = {
  menu: state => state.menu
}

const actions = {}

const mutations = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}