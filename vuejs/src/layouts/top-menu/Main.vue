<template>
  <div v-if="currentUser != null">
    <nav class="am-nav">
      <div class="am-nav-brand">
        <a @click="goTopPage" class="am-nav-logo">
          Anymore Meter
        </a>
      </div>

      <ul class="am-nav-menu">
        <li v-for="(menu, index) in formattedMenu" :key="index">
          <router-link
            :to="{ name: menu.pageName }"
            class="am-nav-link"
            :class="{ 'am-nav-link-active': menu.active }"
          >
            {{ menu.title }}
          </router-link>
        </li>
      </ul>

      <div class="am-nav-user">
        <div class="am-nav-user-info">
          <div class="am-nav-user-name">{{ currentUser.username }}</div>
          <div class="am-nav-user-email">{{ currentUser.email }}</div>
        </div>
        <button @click="logout" class="am-nav-logout">
          ログアウト
        </button>
      </div>
    </nav>

    <main class="am-main">
      <router-view />
    </main>
  </div>
</template>

<script>
import { defineComponent, computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '@/store'
import { helper as $h } from '@/utils/helper'
import { nestedMenu, linkTo } from '@/layouts/side-menu'
import axios from 'axios'

export default defineComponent({
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const formattedMenu = ref([])
    const topMenu = computed(() => nestedMenu(store.state.topMenu.menu, route))
    const currentUser = computed(() => store.getters['users/currentUser'])

    const goTopPage = () => {
      router.push({ name: 'dashboard' })
    }

    const logout = () => {
      localStorage.removeItem('token')
      router.push({ name: 'login' })
    }

    watch(
      computed(() => route.path),
      () => {
        formattedMenu.value = $h.toRaw(topMenu.value)
      }
    )

    onMounted(async () => {
      if (!localStorage.getItem('token')) {
        router.push({ name: 'login' })
        return
      }

      try {
        const response = await axios.get('/api/users/me/', {
          headers: {
            'Authorization': `JWT ${localStorage.getItem('token')}`
          }
        })
        store.dispatch('users/setCurrentUser', response.data)
        formattedMenu.value = $h.toRaw(topMenu.value)
      } catch (error) {
        router.push({ name: 'login' })
      }
    })

    return {
      formattedMenu,
      router,
      linkTo,
      currentUser,
      goTopPage,
      logout
    }
  }
})
</script>