<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-blue-900">
    <div class="am-card w-full max-w-md mx-4">
      <div class="am-card-body p-8">
        <h1 class="am-h2 text-center mb-2">Anymore Meter</h1>
        <p class="am-text text-center mb-8">メーターデータ収集管理システム</p>
        
        <div class="space-y-4">
          <div class="am-form-group">
            <label class="am-label">メールアドレス</label>
            <input type="email" v-model="email" class="am-input" placeholder="email@example.com" />
          </div>
          
          <div class="am-form-group">
            <label class="am-label">パスワード</label>
            <input type="password" v-model="password" class="am-input" placeholder="パスワード" />
          </div>
          
          <div v-if="error" class="am-alert am-alert-danger">
            {{ error }}
          </div>
          
          <button class="am-btn am-btn-primary w-full" @click="login">
            ログイン
          </button>
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