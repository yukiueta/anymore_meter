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
        pageName: 'meters',
        title: 'メーター',
        category: 'meters',
        subMenu: [
          {
            icon: 'ActivityIcon',
            pageName: 'meter-list',
            title: 'メーター一覧'
          },
        ]
      },
      {
        icon: 'BarChart2Icon',
        pageName: 'readings',
        title: 'データ',
        category: 'readings',
        subMenu: [
          {
            icon: 'ActivityIcon',
            pageName: 'reading-list',
            title: 'データ一覧'
          },
        ]
      },
      {
        icon: 'AlertTriangleIcon',
        pageName: 'alerts',
        title: 'アラート',
        category: 'alerts',
        subMenu: [
          {
            icon: 'ActivityIcon',
            pageName: 'alert-list',
            title: 'アラート一覧'
          },
        ]
      },
      {
        icon: 'SettingsIcon',
        pageName: 'settings',
        title: '設定',
        category: 'settings',
        subMenu: [
          {
            icon: 'ActivityIcon',
            pageName: 'user-list',
            title: 'ユーザー一覧'
          },
        ]
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