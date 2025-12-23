<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">メーター一覧</h2>
      <button class="am-btn am-btn-primary" @click="showCreateModal = true">
        + 新規登録
      </button>
    </div>
    
    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>ステータス</th>
            <th>紐付け案件</th>
            <th>最終受信</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="meters.length === 0">
            <td colspan="5">
              <div class="am-empty">
                <div class="am-empty-title">メーターが登録されていません</div>
                <div class="am-empty-text">新規登録ボタンからメーターを追加してください</div>
              </div>
            </td>
          </tr>
          <tr v-for="meter in meters" :key="meter.id">
            <td class="font-medium text-gray-900">{{ meter.meter_id }}</td>
            <td>
              <span :class="statusBadgeClass(meter.status)">
                {{ statusLabel(meter.status) }}
              </span>
            </td>
            <td>{{ meter.project_name || '未割当' }}</td>
            <td>{{ formatDate(meter.last_received_at) }}</td>
            <td>
              <div class="flex gap-2">
                <router-link :to="`/meter/detail/${meter.id}`" class="am-btn am-btn-sm am-btn-outline">詳細</router-link>
                <button class="am-btn am-btn-sm am-btn-danger" @click="deleteMeter(meter.id, meter.meter_id)">削除</button>
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
          <div class="am-modal-title">メーター新規登録</div>
          <button class="am-modal-close" @click="showCreateModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">メーターID</label>
            <input type="text" v-model="newMeter.meter_id" class="am-input" placeholder="MTR-001" />
          </div>
          <div class="am-form-group">
            <label class="am-label">ステータス</label>
            <select v-model="newMeter.status" class="am-select">
              <option value="registered">登録済み</option>
              <option value="active">稼働中</option>
              <option value="inactive">停止中</option>
            </select>
          </div>
          <div v-if="createError" class="am-alert am-alert-danger">
            {{ createError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-secondary" @click="showCreateModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="createMeter" :disabled="creating">
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
    const meters = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const showCreateModal = ref(false)
    const creating = ref(false)
    const createError = ref('')
    const newMeter = ref({ meter_id: '', status: 'registered' })

    const fetchMeters = async (page = 1) => {
      try {
        const response = await axios.get('/api/meters/list/', { params: { page, per_page: 20 } })
        meters.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
      }
    }

    const changePage = (page) => {
      fetchMeters(page)
    }

    const createMeter = async () => {
      if (!newMeter.value.meter_id) {
        createError.value = 'メーターIDを入力してください'
        return
      }
      creating.value = true
      createError.value = ''
      try {
        await axios.post('/api/meters/create/', newMeter.value)
        showCreateModal.value = false
        newMeter.value = { meter_id: '', status: 'registered' }
        fetchMeters(1)
      } catch (error) {
        createError.value = error.response?.data?.message || '登録に失敗しました'
      } finally {
        creating.value = false
      }
    }

    const deleteMeter = async (id, meterId) => {
      if (!confirm(`${meterId}を削除しますか?`)) return
      try {
        await axios.post(`/api/meters/${id}/delete/`)
        fetchMeters(pagination.value.page)
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const statusBadgeClass = (status) => {
      const classes = {
        active: 'am-badge am-badge-success',
        inactive: 'am-badge am-badge-warning',
        offline: 'am-badge am-badge-danger',
        registered: 'am-badge am-badge-gray'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const statusLabel = (status) => {
      const labels = { active: '稼働中', inactive: '停止中', offline: 'オフライン', registered: '登録済み' }
      return labels[status] || status
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    onMounted(() => fetchMeters())

    return {
      meters, pagination, showCreateModal, creating, createError, newMeter,
      fetchMeters, changePage, createMeter, deleteMeter, statusBadgeClass, statusLabel, formatDate
    }
  }
}
</script>