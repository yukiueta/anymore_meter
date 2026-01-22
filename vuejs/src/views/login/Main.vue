<template>
  <div class="login-page">
    <!-- 背景装飾 -->
    <div class="login-bg">
      <div class="login-bg-circle login-bg-circle-1"></div>
      <div class="login-bg-circle login-bg-circle-2"></div>
      <div class="login-bg-circle login-bg-circle-3"></div>
    </div>

    <div class="login-container">
      <!-- ロゴエリア -->
      <div class="login-header">
        <div class="login-logo">
          <svg class="login-logo-icon" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="18" stroke="#00d4aa" stroke-width="3"/>
            <path d="M12 20L18 26L28 14" stroke="#00d4aa" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="login-logo-text">TG Octopus Meter</span>
        </div>
        <p class="login-subtitle">スマートメーター管理システム</p>
      </div>

      <!-- ログインカード -->
      <div class="login-card">
        <h2 class="login-card-title">ログイン</h2>
        
        <div class="login-form">
          <div class="login-field">
            <label class="login-label">メールアドレス</label>
            <div class="login-input-wrapper">
              <svg class="login-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <input 
                type="email" 
                v-model="email" 
                class="login-input" 
                placeholder="email@example.com" 
                @keyup.enter="login" 
              />
            </div>
          </div>
          
          <div class="login-field">
            <label class="login-label">パスワード</label>
            <div class="login-input-wrapper">
              <svg class="login-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input 
                type="password" 
                v-model="password" 
                class="login-input" 
                placeholder="••••••••" 
                @keyup.enter="login" 
              />
            </div>
          </div>
          
          <div v-if="error" class="login-error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {{ error }}
          </div>
          
          <button class="login-btn" @click="login" :disabled="loading">
            <span v-if="loading" class="login-btn-spinner"></span>
            <span v-else>ログイン</span>
          </button>
        </div>
      </div>

      <!-- フッター -->
      <p class="login-footer">
        Powered by <strong>Anymore Inc.</strong>
      </p>
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
    const loading = ref(false)

    const login = async () => {
      if (!email.value || !password.value) {
        error.value = 'メールアドレスとパスワードを入力してください'
        return
      }
      
      loading.value = true
      error.value = ''
      
      try {
        const response = await axios.post('/api/auth/jwt/create/', {
          email: email.value,
          password: password.value
        })
        localStorage.setItem('token', response.data.access)
        localStorage.setItem('refresh_token', response.data.refresh)
        axios.defaults.headers.common['Authorization'] = `JWT ${response.data.access}`
        router.push('/meter/list')
      } catch (err) {
        error.value = 'メールアドレスまたはパスワードが正しくありません'
      } finally {
        loading.value = false
      }
    }

    return {
      email,
      password,
      error,
      loading,
      login
    }
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0d001a 0%, #1a0033 50%, #2d0052 100%);
  position: relative;
  overflow: hidden;
}

// 背景の装飾円
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.login-bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.login-bg-circle-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #e91e8c 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.login-bg-circle-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #00d4aa 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.login-bg-circle-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #e91e8c 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-30px) rotate(5deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.1; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.2; transform: translate(-50%, -50%) scale(1.1); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 2rem;
}

// ロゴエリア
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.login-logo-icon {
  width: 40px;
  height: 40px;
}

.login-logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  letter-spacing: -0.025em;
}

.login-subtitle {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

// ログインカード
.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 1.5rem;
  padding: 2.5rem;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.login-card-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a0033;
  text-align: center;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.login-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #616161;
}

.login-input-wrapper {
  position: relative;
}

.login-input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1.25rem;
  height: 1.25rem;
  color: #9e9e9e;
  pointer-events: none;
}

.login-input {
  width: 100%;
  padding: 0.875rem 1rem 0.875rem 3rem;
  font-size: 1rem;
  color: #212121;
  background: #fafafa;
  border: 2px solid #e0e0e0;
  border-radius: 0.75rem;
  transition: all 0.2s;

  &::placeholder {
    color: #bdbdbd;
  }

  &:focus {
    outline: none;
    background: white;
    border-color: #e91e8c;
    box-shadow: 0 0 0 4px rgba(233, 30, 140, 0.1);
  }
}

.login-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1rem;
  background: #ffe8ea;
  border-radius: 0.75rem;
  color: #cc3945;
  font-size: 0.875rem;
  font-weight: 500;

  svg {
    width: 1.25rem;
    height: 1.25rem;
    flex-shrink: 0;
  }
}

.login-btn {
  width: 100%;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #e91e8c 0%, #c4177a 100%);
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #f74da8 0%, #e91e8c 100%);
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -5px rgba(233, 30, 140, 0.4);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.login-btn-spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// フッター
.login-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
  margin-top: 2rem;

  strong {
    color: rgba(255, 255, 255, 0.6);
  }
}
</style>