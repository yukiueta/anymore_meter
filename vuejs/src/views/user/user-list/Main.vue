<template>
  <div>
    <h2 class="text-lg font-medium mt-10">ユーザー一覧</h2>
    <div class="box p-5 mt-5">
      <div class="flex justify-end mb-5">
        <button class="btn btn-primary" @click="showCreateModal = true">新規登録</button>
      </div>
      <table class="table table-report">
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
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ permissionLabel(user.permission) }}</td>
            <td>
              <span :class="user.is_active ? 'text-success' : 'text-danger'">
                {{ user.is_active ? '有効' : '無効' }}
              </span>
            </td>
            <td>
              <router-link :to="`/user/detail/${user.id}`" class="btn btn-sm btn-outline-primary">詳細</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const users = ref([])
    const showCreateModal = ref(false)

    const fetchUsers = async () => {
      try {
        const response = await axios.get('/api/users/list/')
        users.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const permissionLabel = (permission) => {
      const labels = {
        admin: '管理者',
        staff: 'スタッフ'
      }
      return labels[permission] || permission
    }

    onMounted(() => {
      fetchUsers()
    })

    return {
      users,
      showCreateModal,
      permissionLabel
    }
  }
}
</script>