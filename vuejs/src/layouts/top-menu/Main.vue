<template>
  <div v-if="currentUser != null">
    <nav class="am-nav">
      <div class="am-nav-brand">
        <a @click="goTopPage" class="am-nav-logo">
          <svg class="am-nav-logo-icon" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="12" r="8" fill="#e91e8c"/>
            <ellipse cx="16" cy="12" rx="3" ry="2" fill="#ffffff" opacity="0.3"/>
            <path d="M8 20c-1 2-2 8 0 8s2-4 3-6" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M12 22c0 2-1 6 1 6s2-4 2-6" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M18 22c0 2 1 6-1 6s-2-4-2-6" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M24 20c1 2 2 8 0 8s-2-4-3-6" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
          <div class="am-nav-logo-content">
            <span class="am-nav-logo-title">TG Octopus</span>
            <span class="am-nav-logo-subtitle">Meter Management</span>
          </div>
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

      <span class="am-nav-powered">powered by <a href="https://anymore.co.jp" target="_blank">Anymore</a></span>

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
      router.push({ name: 'meter-list' })
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