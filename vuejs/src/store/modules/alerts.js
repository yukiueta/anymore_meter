const state = () => {
  return {
    alerts: [],
    loading: false
  }
}

const getters = {
  alerts: state => state.alerts,
  loading: state => state.loading
}

const actions = {
  setAlerts({ commit }, alerts) {
    commit('SET_ALERTS', alerts)
  },
  setLoading({ commit }, loading) {
    commit('SET_LOADING', loading)
  }
}

const mutations = {
  SET_ALERTS(state, alerts) {
    state.alerts = alerts
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}