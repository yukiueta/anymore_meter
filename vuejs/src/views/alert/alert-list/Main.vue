<template>
  <div class="p-6">
    <h2 class="am-h2 mb-6">アラート一覧</h2>
    
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">ステータス</label>
        <select v-model="selectedStatus" class="am-filter-select">
          <option value="">全ステータス</option>
          <option value="open">発生中</option>
          <option value="resolved">解決済</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">種別</label>
        <select v-model="selectedType" class="am-filter-select">
          <option value="">全種別</option>
          <option value="communication">通信途絶</option>
          <option value="anomaly">異常値</option>
        </select>
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-ghost" @click="resetFilter">リセット</button>
        <button class="am-btn am-btn-primary" @click="search">検索</button>
      </div>
    </div>

    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th>日時</th>
            <th>メーターID</th>
            <th>種別</th>
            <th>ステータス</th>
            <th>メッセージ</th>
            <th>メモ</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="alerts.length === 0">
            <td colspan="7">
              <div class="am-empty">
                <div class="am-empty-title">アラートがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="alert in alerts" :key="alert.id">
            <td>{{ formatDateTime(alert.detected_at) }}</td>
            <td class="font-medium text-gray-900">{{ alert.meter_id }}</td>
            <td>
              <span class="am-badge am-badge-gray">{{ typeLabel(alert.alert_type) }}</span>
            </td>
            <td>
              <span :class="statusBadgeClass(alert.status)">{{ statusLabel(alert.status) }}</span>
            </td>
            <td class="max-w-xs truncate">{{ alert.message }}</td>
            <td class="max-w-xs truncate text-gray-500 text-sm">{{ alert.note }}</td>
            <td>
              <button v-if="alert.status === 'open'" class="am-btn am-btn-sm am-btn-success" @click="openResolveModal(alert)">解決</button>
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

    <!-- 解決モーダル -->
    <div v-if="showResolveModal" class="am-modal-overlay" @click.self="showResolveModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">アラート解決</div>
          <button class="am-modal-close" @click="showResolveModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">メモ（任意）</label>
            <textarea v-model="resolveNote" class="am-textarea" rows="3" placeholder="対応内容を記入してください"></textarea>
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showResolveModal = false">キャンセル</button>
          <button class="am-btn am-btn-success" @click="resolve" :disabled="resolving">
            {{ resolving ? '処理中...' : '解決' }}
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
import { formatDateTime } from '@/utils/date'

export default {
  components: { Pagination },
  setup() {
    const alerts = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const selectedStatus = ref('')
    const selectedType = ref('')
    const showResolveModal = ref(false)
    const resolveNote = ref('')
    const resolveTargetId = ref(null)
    const resolving = ref(false)

    const fetchAlerts = async (page = 1) => {
      try {
        const params = { page, per_page: 20 }
        if (selectedStatus.value) params.status = selectedStatus.value
        if (selectedType.value) params.type = selectedType.value
        const response = await axios.get('/api/alerts/list/', { params })
        alerts.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
      }
    }

    const search = () => fetchAlerts(1)

    const resetFilter = () => {
      selectedStatus.value = ''
      selectedType.value = ''
      fetchAlerts(1)
    }

    const changePage = (page) => fetchAlerts(page)

    const openResolveModal = (alert) => {
      resolveTargetId.value = alert.id
      resolveNote.value = ''
      showResolveModal.value = true
    }

    const resolve = async () => {
      resolving.value = true
      try {
        await axios.post(`/api/alerts/${resolveTargetId.value}/resolve/`, { note: resolveNote.value })
        showResolveModal.value = false
        fetchAlerts(pagination.value.page)
      } catch (error) {
        console.error(error)
      } finally {
        resolving.value = false
      }
    }

    const typeLabel = (type) => {
      const labels = { communication: '通信途絶', anomaly: '異常値' }
      return labels[type] || type
    }

    const statusBadgeClass = (status) => {
      const classes = {
        open: 'am-badge am-badge-danger',
        resolved: 'am-badge am-badge-success'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const statusLabel = (status) => {
      const labels = { open: '発生中', resolved: '解決済' }
      return labels[status] || status
    }

    onMounted(() => fetchAlerts())

    return {
      alerts,
      pagination,
      selectedStatus,
      selectedType,
      showResolveModal,
      resolveNote,
      resolving,
      search,
      resetFilter,
      changePage,
      openResolveModal,
      resolve,
      typeLabel,
      statusBadgeClass,
      statusLabel,
      formatDateTime
    }
  }
}
</script>