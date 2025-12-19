const state = () => {
  return {
    meters: [],
    meter: null,
    loading: false
  }
}

const getters = {
  meters: state => state.meters,
  meter: state => state.meter,
  loading: state => state.loading
}

const actions = {
  setMeters({ commit }, meters) {
    commit('SET_METERS', meters)
  },
  setMeter({ commit }, meter) {
    commit('SET_METER', meter)
  },
  setLoading({ commit }, loading) {
    commit('SET_LOADING', loading)
  }
}

const mutations = {
  SET_METERS(state, meters) {
    state.meters = meters
  },
  SET_METER(state, meter) {
    state.meter = meter
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