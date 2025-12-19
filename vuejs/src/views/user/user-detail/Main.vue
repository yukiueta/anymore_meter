<template>
  <div>
    <h2 class="text-lg font-medium mt-10">ユーザー詳細</h2>
    <div class="box p-5 mt-5" v-if="user">
      <table class="table">
        <tr>
          <th class="w-40">ユーザー名</th>
          <td>{{ user.username }}</td>
        </tr>
        <tr>
          <th>メールアドレス</th>
          <td>{{ user.email }}</td>
        </tr>
        <tr>
          <th>権限</th>
          <td>{{ permissionLabel(user.permission) }}</td>
        </tr>
        <tr>
          <th>ステータス</th>
          <td>{{ user.is_active ? '有効' : '無効' }}</td>
        </tr>
        <tr>
          <th>登録日</th>
          <td>{{ formatDate(user.date_joined) }}</td>
        </tr>
      </table>
      <div class="mt-5">
        <button class="btn btn-primary mr-2" @click="showEditModal = true">編集</button>
        <button class="btn btn-danger" @click="deleteUser">削除</button>
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

    const fetchUser = async () => {
      try {
        const response = await axios.get(`/api/users/${route.params.pk}/detail/`)
        user.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const deleteUser = async () => {
      if (!confirm('削除しますか?')) return
      try {
        await axios.post(`/api/users/${route.params.pk}/delete/`)
        router.push('/user/list')
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
      deleteUser,
      permissionLabel,
      formatDate
    }
  }
}
</script>