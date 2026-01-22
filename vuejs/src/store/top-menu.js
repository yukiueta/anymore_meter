const state = () => {
  return {
    menu: [
      {
        icon: 'CpuIcon',
        pageName: 'meter-list',
        title: 'メーター',
        category: 'meters'
      },
      {
        icon: 'BarChart2Icon',
        pageName: 'reading-list',
        title: '30分データ',
        category: 'readings'
      },
      {
        icon: 'BarChartIcon',
        pageName: 'billing-summary',
        title: '請求データ',
        category: 'billing'  // ← 追加
      },
      {
        icon: 'AlertTriangleIcon',
        pageName: 'alert-list',
        title: 'アラート',
        category: 'alerts'
      },
      {
        icon: 'CalendarIcon',
        pageName: 'billing-calendar',
        title: '検針日',
        category: 'billing'  // ← 追加
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