<template>
  <div class="login">
    <div class="container sm:px-10">
      <div class="block xl:grid grid-cols-2 gap-4">
        <div class="hidden xl:flex flex-col min-h-screen">
          <div class="my-auto">
            <div class="text-white font-medium text-4xl leading-tight mt-10">
              Anymore Meter
            </div>
            <div class="text-white text-opacity-70 mt-5">
              メーターデータ収集管理システム
            </div>
          </div>
        </div>
        <div class="h-screen xl:h-auto flex py-5 xl:py-0 my-10 xl:my-0">
          <div class="my-auto mx-auto xl:ml-20 bg-white px-5 sm:px-8 py-8 rounded-md shadow-md w-full sm:w-3/4 lg:w-2/4 xl:w-auto">
            <h2 class="text-2xl font-bold text-center">ログイン</h2>
            <div class="mt-8">
              <input type="email" v-model="email" class="form-control py-3 px-4 block" placeholder="メールアドレス" />
              <input type="password" v-model="password" class="form-control py-3 px-4 block mt-4" placeholder="パスワード" />
              <button class="btn btn-primary py-3 px-4 w-full mt-5" @click="login">ログイン</button>
              <p v-if="error" class="text-danger mt-3 text-center">{{ error }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const router = useRouter()
    const email = ref('')
    const password = ref('')
    const error = ref('')

    const login = async () => {
      try {
        const response = await axios.post('/api/auth/jwt/create/', {
          email: email.value,
          password: password.value
        })
        localStorage.setItem('token', response.data.access)
        axios.defaults.headers.common['Authorization'] = `JWT ${response.data.access}`
        router.push('/')
      } catch (err) {
        error.value = 'メールアドレスまたはパスワードが正しくありません'
      }
    }

    return {
      email,
      password,
      error,
      login
    }
  }
}
</script>