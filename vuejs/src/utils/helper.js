//vuejs/src/utils/helper.js
const helpers = {
  isset(obj) {
    if (obj !== null && obj !== undefined) {
      if (typeof obj === 'object' || Array.isArray(obj)) {
        return Object.keys(obj).length
      } else {
        return obj.toString().length
      }
    }

    return false
  },
  toRaw(obj) {
    return JSON.parse(JSON.stringify(obj))
  }
}

const install = app => {
  app.config.globalProperties.$h = helpers
}

export { install as default, helpers as helper }
