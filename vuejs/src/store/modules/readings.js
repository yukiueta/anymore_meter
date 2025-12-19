const state = () => {
  return {
    readings: [],
    dailySummaries: [],
    monthlySummaries: [],
    loading: false
  }
}

const getters = {
  readings: state => state.readings,
  dailySummaries: state => state.dailySummaries,
  monthlySummaries: state => state.monthlySummaries,
  loading: state => state.loading
}

const actions = {
  setReadings({ commit }, readings) {
    commit('SET_READINGS', readings)
  },
  setDailySummaries({ commit }, summaries) {
    commit('SET_DAILY_SUMMARIES', summaries)
  },
  setMonthlySummaries({ commit }, summaries) {
    commit('SET_MONTHLY_SUMMARIES', summaries)
  },
  setLoading({ commit }, loading) {
    commit('SET_LOADING', loading)
  }
}

const mutations = {
  SET_READINGS(state, readings) {
    state.readings = readings
  },
  SET_DAILY_SUMMARIES(state, summaries) {
    state.dailySummaries = summaries
  },
  SET_MONTHLY_SUMMARIES(state, summaries) {
    state.monthlySummaries = summaries
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