<template>
  <div v-if="currentUser != null">
    <div class="top-menu-container">
      <nav class="top-nav flex items-center">
        <div class="logo-area">
          <a @click="goTopPage" class="logo-link" style="cursor: pointer;">
            <span class="text-white font-bold text-xl">Anymore Meter</span>
          </a>
        </div>

        <ul class="nav-list ml-2 mr-auto">
          <template v-for="(menu, menuKey) in formattedMenu" :key="menuKey">
            <li>
              <a
                :href="menu.subMenu ? 'javascript:;' : router.resolve({ name: menu.pageName }).path"
                class="top-menu"
                :class="{ 'top-menu--active': menu.active }"
                @click="linkTo(menu, router, $event)"
              >
                <div class="h-6 top-menu__title text-sm">
                  {{ menu.title }}
                  <ChevronDownIcon v-if="menu.subMenu" class="top-menu__sub-icon" />
                </div>
              </a>
              <ul v-if="menu.subMenu">
                <template v-for="(subMenu, subMenuKey) in menu.subMenu" :key="subMenuKey">
                  <li :class="[subMenu.active ? ['bg-theme-1'] : []]">
                    <a
                      :href="router.resolve({ name: subMenu.pageName }).path"
                      class="top-menu"
                      :class="[subMenu.active ? ['text-white', 'font-extrabold'] : ['text-gray-600', 'font-normal']]"
                      @click="linkTo(subMenu, router, $event)"
                    >
                      <div class="top-menu__icon">
                        <component class="w-4" :is="subMenu.icon" />
                      </div>
                      <div class="ml-1 top-menu__title text-sm">
                        {{ subMenu.title }}
                      </div>
                    </a>
                  </li>
                </template>
              </ul>
            </li>
          </template>
        </ul>

        <div class="intro-x dropdown flex items-center">
          <div class="dropdown-toggle" role="button" aria-expanded="false">
            <div class="text-white font-bold">{{ currentUser.username }}</div>
            <div class="mt-1 text-white text-xs">{{ currentUser.email }}</div>
          </div>
          <div class="dropdown-menu w-56">
            <div class="dropdown-menu__content box bg-theme-11 text-white">
              <div class="p-4 border-b border-theme-12">
                <div class="font-medium">{{ currentUser.username }}</div>
                <div class="text-xs text-theme-13 mt-0.5">{{ currentUser.email }}</div>
              </div>
              <div class="p-2 border-t border-theme-12">
                <a
                  @click="logout"
                  class="flex items-center block p-2 transition duration-300 ease-in-out hover:bg-theme-1 rounded-md cursor-pointer"
                >
                  <ToggleRightIcon class="w-4 h-4 mr-2" /> ログアウト
                </a>
              </div>
            </div>
          </div>
        </div>
      </nav>
    </div>

    <div class="wrapper">
      <div class="wrapper-box">
        <div class="content bg-gray-200 overflow-y-auto" style="height: 94svh">
          <router-view />
        </div>
      </div>
    </div>
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
      console.log('top-menu mounted')
      console.log('token:', localStorage.getItem('token'))
      
      if (!localStorage.getItem('token')) {
        console.log('no token, redirect to login')
        router.push({ name: 'login' })
        return
      }

      try {
        console.log('fetching user')
        const response = await axios.get('/api/users/me/', {
          headers: {
            'Authorization': `JWT ${localStorage.getItem('token')}`
          }
        })
        console.log('user response:', response)
        store.dispatch('users/setCurrentUser', response.data)
        formattedMenu.value = $h.toRaw(topMenu.value)
      } catch (error) {
        console.log('fetch error:', error)
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

<style>
:root {
  --primary-navy: #11296d;
  --primary-blue: #008bf2;
  --bg-primary: #11296d;
  --text-primary: #ffffff;
  --transition: 0.2s ease-in-out;
}

.top-nav {
  background: linear-gradient(135deg, #0a1d57 0%, #10296D 40%, #1a3a82 100%) !important;
  box-shadow: 0 2px 12px rgba(16, 41, 109, 0.3) !important;
  padding: 0 1rem;
  height: 60px;
}

.logo-area {
  height: 100%;
  display: flex;
  align-items: center;
  padding-right: 1.5rem;
  margin-right: 0.5rem;
  position: relative;
}

.logo-area::after {
  content: '';
  position: absolute;
  right: 0;
  top: 20px;
  bottom: 20px;
  width: 1px;
  background: rgba(255, 255, 255, 0.15);
}

.logo-link {
  display: flex;
  align-items: center;
  height: 100%;
  transition: opacity var(--transition);
}

.logo-link:hover {
  opacity: 0.9;
}

.nav-list {
  height: 100%;
  display: flex;
  align-items: center;
  margin: 0;
  padding: 0;
  list-style: none;
  gap: 0.25rem;
}

.wrapper {
  padding-top: 60px;
}
</style>