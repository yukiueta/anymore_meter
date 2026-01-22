<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">ユーザー一覧</h2>
      <button class="am-btn am-btn-primary" @click="openCreateModal">
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
            <th>登録日</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="users.length === 0">
            <td colspan="6">
              <div class="am-empty">
                <div class="am-empty-title">ユーザーが登録されていません</div>
              </div>
            </td>
          </tr>
          <tr v-for="user in users" :key="user.id">
            <td class="font-medium text-gray-900">{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="permissionBadgeClass(user.permission)">{{ permissionLabel(user.permission) }}</span>
            </td>
            <td>
              <span :class="user.is_active ? 'am-badge am-badge-success' : 'am-badge am-badge-danger'">
                {{ user.is_active ? '有効' : '無効' }}
              </span>
            </td>
            <td>{{ formatDate(user.date_joined) }}</td>
            <td>
              <div class="flex gap-2">
                <button class="am-btn am-btn-sm am-btn-secondary" @click="openEditModal(user)">編集</button>
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
            <input type="text" v-model="createForm.username" class="am-input" placeholder="ユーザー名" />
          </div>
          <div class="am-form-group">
            <label class="am-label">メールアドレス</label>
            <input type="email" v-model="createForm.email" class="am-input" placeholder="email@example.com" />
          </div>
          <div class="am-form-group">
            <label class="am-label">パスワード</label>
            <input type="password" v-model="createForm.password" class="am-input" placeholder="パスワード（8文字以上）" />
          </div>
          <div class="am-form-group">
            <label class="am-label">権限</label>
            <select v-model="createForm.permission" class="am-select">
              <option value="operator">オペレーター</option>
              <option value="admin">管理者</option>
            </select>
          </div>
          <div v-if="createError" class="am-alert am-alert-danger">
            {{ createError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showCreateModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="createUser" :disabled="creating">
            {{ creating ? '登録中...' : '登録' }}
          </button>
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
              <option value="operator">オペレーター</option>
              <option value="admin">管理者</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-checkbox">
              <input type="checkbox" v-model="editForm.is_active" />
              <span>有効</span>
            </label>
          </div>
          <div v-if="editError" class="am-alert am-alert-danger">
            {{ editError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showEditModal = false">キャンセル</button>
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
import axios from 'axios'
import Pagination from '@/components/Pagination.vue'
import { formatDate } from '@/utils/date'

export default {
  components: { Pagination },
  setup() {
    const users = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    
    // 新規登録
    const showCreateModal = ref(false)
    const creating = ref(false)
    const createError = ref('')
    const createForm = ref({ username: '', email: '', password: '', permission: 'operator' })
    
    // 編集
    const showEditModal = ref(false)
    const updating = ref(false)
    const editError = ref('')
    const editForm = ref({ id: null, username: '', email: '', permission: 'operator', is_active: true })

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

    const openCreateModal = () => {
      createForm.value = { username: '', email: '', password: '', permission: 'operator' }
      createError.value = ''
      showCreateModal.value = true
    }

    const createUser = async () => {
      if (!createForm.value.username || !createForm.value.email || !createForm.value.password) {
        createError.value = '全ての項目を入力してください'
        return
      }
      if (createForm.value.password.length < 8) {
        createError.value = 'パスワードは8文字以上必要です'
        return
      }
      creating.value = true
      createError.value = ''
      try {
        await axios.post('/api/users/create/', createForm.value)
        showCreateModal.value = false
        fetchUsers(1)
      } catch (error) {
        createError.value = error.response?.data?.error || '登録に失敗しました'
      } finally {
        creating.value = false
      }
    }

    const openEditModal = (user) => {
      editForm.value = {
        id: user.id,
        username: user.username,
        email: user.email,
        permission: user.permission || 'operator',
        is_active: user.is_active
      }
      editError.value = ''
      showEditModal.value = true
    }

    const updateUser = async () => {
      updating.value = true
      editError.value = ''
      try {
        await axios.post(`/api/users/${editForm.value.id}/update/`, {
          username: editForm.value.username,
          email: editForm.value.email,
          permission: editForm.value.permission,
          is_active: editForm.value.is_active
        })
        showEditModal.value = false
        fetchUsers(pagination.value.page)
      } catch (error) {
        editError.value = error.response?.data?.error || '更新に失敗しました'
      } finally {
        updating.value = false
      }
    }

    const deleteUser = async (id, username) => {
      if (!confirm(`${username}を削除しますか?`)) return
      try {
        await axios.post(`/api/users/${id}/delete/`)
        fetchUsers(pagination.value.page)
      } catch (error) {
        alert(error.response?.data?.error || '削除に失敗しました')
      }
    }

    const permissionLabel = (permission) => {
      const labels = { admin: '管理者', operator: 'オペレーター' }
      return labels[permission] || permission
    }

    const permissionBadgeClass = (permission) => {
      return permission === 'admin' ? 'am-badge am-badge-purple' : 'am-badge am-badge-gray'
    }

    onMounted(() => fetchUsers())

    return {
      users,
      pagination,
      showCreateModal,
      creating,
      createError,
      createForm,
      showEditModal,
      updating,
      editError,
      editForm,
      changePage,
      openCreateModal,
      createUser,
      openEditModal,
      updateUser,
      deleteUser,
      permissionLabel,
      permissionBadgeClass,
      formatDate
    }
  }
}
</script>