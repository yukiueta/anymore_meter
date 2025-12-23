<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">ユーザー詳細</h2>
      <router-link to="/user/list" class="am-btn am-btn-secondary">
        ← 一覧に戻る
      </router-link>
    </div>
    
    <div class="am-card max-w-2xl" v-if="user">
      <div class="am-card-header">
        <div class="am-card-title">ユーザー情報</div>
      </div>
      <div class="am-card-body">
        <dl class="space-y-4">
          <div class="flex">
            <dt class="am-label w-40">ユーザー名</dt>
            <dd class="am-text font-medium text-gray-900">{{ user.username }}</dd>
          </div>
          <div class="flex">
            <dt class="am-label w-40">メールアドレス</dt>
            <dd class="am-text">{{ user.email }}</dd>
          </div>
          <div class="flex">
            <dt class="am-label w-40">権限</dt>
            <dd>
              <span class="am-badge am-badge-info">{{ permissionLabel(user.permission) }}</span>
            </dd>
          </div>
          <div class="flex">
            <dt class="am-label w-40">ステータス</dt>
            <dd>
              <span :class="user.is_active ? 'am-badge am-badge-success' : 'am-badge am-badge-danger'">
                {{ user.is_active ? '有効' : '無効' }}
              </span>
            </dd>
          </div>
          <div class="flex">
            <dt class="am-label w-40">登録日</dt>
            <dd class="am-text">{{ formatDate(user.date_joined) }}</dd>
          </div>
        </dl>
      </div>
      <div class="am-card-footer">
        <div class="flex gap-2">
          <button class="am-btn am-btn-primary" @click="openEditModal">編集</button>
          <button class="am-btn am-btn-danger" @click="deleteUser">削除</button>
        </div>
      </div>
    </div>

    <!-- 編集モーダル -->
    <div v-if="showEditModal" class="am-modal-overlay" @click.self="showEditModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">ユーザー編集</div>
          <button class="am-modal-close" @click="showEditModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">ユーザー名</label>
            <input type="text" v-model="editForm.username" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">メールアドレス</label>
            <input type="email" v-model="editForm.email" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">権限</label>
            <select v-model="editForm.permission" class="am-select">
              <option value="staff">スタッフ</option>
              <option value="admin">管理者</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">ステータス</label>
            <label class="am-toggle">
              <input type="checkbox" v-model="editForm.is_active" />
              <span class="am-toggle-slider"></span>
              <span class="am-toggle-label">{{ editForm.is_active ? '有効' : '無効' }}</span>
            </label>
          </div>
          <div v-if="editError" class="am-alert am-alert-danger">
            {{ editError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-secondary" @click="showEditModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="updateUser" :disabled="updating">
            {{ updating ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const route = useRoute()
    const router = useRouter()
    const user = ref(null)
    const showEditModal = ref(false)
    const updating = ref(false)
    const editError = ref('')
    const editForm = ref({
      username: '',
      email: '',
      permission: 'staff',
      is_active: true
    })

    const fetchUser = async () => {
      try {
        const response = await axios.get(`/api/users/${route.params.pk}/detail/`)
        user.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const openEditModal = () => {
      editForm.value = {
        username: user.value.username,
        email: user.value.email,
        permission: user.value.permission || 'staff',
        is_active: user.value.is_active
      }
      editError.value = ''
      showEditModal.value = true
    }

    const updateUser = async () => {
      updating.value = true
      editError.value = ''
      
      try {
        await axios.post(`/api/users/${route.params.pk}/update/`, editForm.value)
        showEditModal.value = false
        fetchUser()
      } catch (error) {
        editError.value = error.response?.data?.message || '更新に失敗しました'
      } finally {
        updating.value = false
      }
    }

    const deleteUser = async () => {
      if (!confirm('このユーザーを削除しますか?')) return
      
      try {
        await axios.post(`/api/users/${route.params.pk}/delete/`)
        router.push('/user/list')
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const permissionLabel = (permission) => {
      const labels = {
        admin: '管理者',
        staff: 'スタッフ'
      }
      return labels[permission] || permission
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    onMounted(() => {
      fetchUser()
    })

    return {
      user,
      showEditModal,
      updating,
      editError,
      editForm,
      openEditModal,
      updateUser,
      deleteUser,
      permissionLabel,
      formatDate
    }
  }
}
</script>