import Chart from './chart/Main.vue'
import Tippy from './tippy/Main.vue'
import LoadingIcon from './loading-icon/Main.vue'
import * as featherIcons from '@zhuowenli/vue-feather-icons'

export default app => {
  app.component('Chart', Chart)
  app.component('Tippy', Tippy)
  app.component('LoadingIcon', LoadingIcon)

  for (const [key, icon] of Object.entries(featherIcons)) {
    icon.props.size.default = '36'
    app.component(key, icon)
  }
}