<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">ユーザー一覧</h2>
      <button class="am-btn am-btn-primary" @click="showCreateModal = true">
        + 新規登録
      </button>
    </div>
    
    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th>ユーザー名</th>
            <th>メールアドレス</th>
            <th>権限</th>
            <th>ステータス</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="users.length === 0">
            <td colspan="5">
              <div class="am-empty">
                <div class="am-empty-title">ユーザーが登録されていません</div>
              </div>
            </td>
          </tr>
          <tr v-for="user in users" :key="user.id">
            <td class="font-medium text-gray-900">{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="am-badge am-badge-info">{{ permissionLabel(user.permission) }}</span>
            </td>
            <td>
              <span :class="user.is_active ? 'am-badge am-badge-success' : 'am-badge am-badge-danger'">
                {{ user.is_active ? '有効' : '無効' }}
              </span>
            </td>
            <td>
              <div class="flex gap-2">
                <router-link :to="`/user/detail/${user.id}`" class="am-btn am-btn-sm am-btn-outline">詳細</router-link>
                <button class="am-btn am-btn-sm am-btn-danger" @click="deleteUser(user.id, user.username)">削除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div class="p-4 border-t">
        <Pagination
          :current-page="pagination.page"
          :total-pages="pagination.total_pages"
          :total="pagination.total"
          :per-page="pagination.per_page"
          @change="changePage"
        />
      </div>
    </div>

    <!-- 新規登録モーダル -->
    <div v-if="showCreateModal" class="am-modal-overlay" @click.self="showCreateModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">ユーザー新規登録</div>
          <button class="am-modal-close" @click="showCreateModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">ユーザー名</label>
            <input type="text" v-model="newUser.username" class="am-input" placeholder="ユーザー名" />
          </div>
          <div class="am-form-group">
            <label class="am-label">メールアドレス</label>
            <input type="email" v-model="newUser.email" class="am-input" placeholder="email@example.com" />
          </div>
          <div class="am-form-group">
            <label class="am-label">パスワード</label>
            <input type="password" v-model="newUser.password" class="am-input" placeholder="パスワード" />
          </div>
          <div class="am-form-group">
            <label class="am-label">権限</label>
            <select v-model="newUser.permission" class="am-select">
              <option value="staff">スタッフ</option>
              <option value="admin">管理者</option>
            </select>
          </div>
          <div v-if="createError" class="am-alert am-alert-danger">
            {{ createError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-secondary" @click="showCreateModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="createUser" :disabled="creating">
            {{ creating ? '登録中...' : '登録' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Pagination from '@/components/Pagination.vue'

export default {
  components: { Pagination },
  setup() {
    const users = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const showCreateModal = ref(false)
    const creating = ref(false)
    const createError = ref('')
    const newUser = ref({ username: '', email: '', password: '', permission: 'staff' })

    const fetchUsers = async (page = 1) => {
      try {
        const response = await axios.get('/api/users/list/', { params: { page, per_page: 20 } })
        users.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
      }
    }

    const changePage = (page) => {
      fetchUsers(page)
    }

    const createUser = async () => {
      if (!newUser.value.username || !newUser.value.email || !newUser.value.password) {
        createError.value = '全ての項目を入力してください'
        return
      }
      creating.value = true
      createError.value = ''
      try {
        await axios.post('/api/users/create/', newUser.value)
        showCreateModal.value = false
        newUser.value = { username: '', email: '', password: '', permission: 'staff' }
        fetchUsers(1)
      } catch (error) {
        createError.value = error.response?.data?.message || '登録に失敗しました'
      } finally {
        creating.value = false
      }
    }

    const deleteUser = async (id, username) => {
      if (!confirm(`${username}を削除しますか?`)) return
      try {
        await axios.post(`/api/users/${id}/delete/`)
        fetchUsers(pagination.value.page)
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const permissionLabel = (permission) => {
      const labels = { admin: '管理者', staff: 'スタッフ' }
      return labels[permission] || permission
    }

    onMounted(() => fetchUsers())

    return {
      users,
      pagination,
      showCreateModal,
      creating,
      createError,
      newUser,
      fetchUsers,
      changePage,
      createUser,
      deleteUser,
      permissionLabel
    }
  }
}
</script>