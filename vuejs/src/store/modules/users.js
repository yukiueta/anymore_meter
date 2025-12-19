const state = () => {
  return {
    users: [],
    currentUser: null,
    loading: false
  }
}

const getters = {
  users: state => state.users,
  currentUser: state => state.currentUser,
  loading: state => state.loading
}

const actions = {
  setUsers({ commit }, users) {
    commit('SET_USERS', users)
  },
  setCurrentUser({ commit }, user) {
    commit('SET_CURRENT_USER', user)
  },
  setLoading({ commit }, loading) {
    commit('SET_LOADING', loading)
  }
}

const mutations = {
  SET_USERS(state, users) {
    state.users = users
  },
  SET_CURRENT_USER(state, user) {
    state.currentUser = user
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
