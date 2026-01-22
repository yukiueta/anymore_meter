<template>
  <div class="p-6">
    <h2 class="am-h2 mb-6">アラート一覧</h2>
    
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">ステータス</label>
        <select v-model="selectedStatus" class="am-filter-select">
          <option value="">全ステータス</option>
          <option value="open">未対応</option>
          <option value="acknowledged">確認済</option>
          <option value="resolved">解決済</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">種別</label>
        <select v-model="selectedType" class="am-filter-select">
          <option value="">全種別</option>
          <option value="communication">通信途絶</option>
          <option value="data_missing">データ欠損</option>
          <option value="anomaly">異常値</option>
        </select>
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-ghost" @click="resetFilter">リセット</button>
        <button class="am-btn am-btn-primary" @click="search">検索</button>
      </div>
    </div>
    
    <!-- 一括操作 -->
    <div v-if="selectedAlerts.length > 0" class="mb-4 p-4 bg-blue-50 rounded-lg flex items-center justify-between">
      <span class="text-blue-800">{{ selectedAlerts.length }}件選択中</span>
      <div class="flex gap-2">
        <button class="am-btn am-btn-sm am-btn-secondary" @click="bulkAcknowledge">一括確認</button>
        <button class="am-btn am-btn-sm am-btn-success" @click="bulkResolve">一括解決</button>
        <button class="am-btn am-btn-sm am-btn-ghost" @click="selectedAlerts = []">選択解除</button>
      </div>
    </div>
    
    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th class="w-10">
              <input type="checkbox" @change="toggleAll" :checked="isAllSelected" />
            </th>
            <th>日時</th>
            <th>メーターID</th>
            <th>種別</th>
            <th>ステータス</th>
            <th>メッセージ</th>
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
          <tr v-for="alert in alerts" :key="alert.id" :class="{ 'bg-blue-50': selectedAlerts.includes(alert.id) }">
            <td>
              <input type="checkbox" :value="alert.id" v-model="selectedAlerts" />
            </td>
            <td>{{ formatDateTime(alert.detected_at) }}</td>
            <td class="font-medium text-gray-900">{{ alert.meter_id }}</td>
            <td>
              <span class="am-badge am-badge-gray">{{ typeLabel(alert.alert_type) }}</span>
            </td>
            <td>
              <span :class="statusBadgeClass(alert.status)">{{ statusLabel(alert.status) }}</span>
            </td>
            <td class="max-w-xs truncate">{{ alert.message }}</td>
            <td>
              <div class="flex gap-2">
                <button v-if="alert.status === 'open'" class="am-btn am-btn-sm am-btn-secondary" @click="acknowledge(alert.id)">確認</button>
                <button v-if="alert.status !== 'resolved'" class="am-btn am-btn-sm am-btn-success" @click="resolve(alert.id)">解決</button>
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
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
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
    const selectedAlerts = ref([])

    const isAllSelected = computed(() => {
      return alerts.value.length > 0 && alerts.value.every(a => selectedAlerts.value.includes(a.id))
    })

    const fetchAlerts = async (page = 1) => {
      try {
        const params = { page, per_page: 20 }
        if (selectedStatus.value) params.status = selectedStatus.value
        if (selectedType.value) params.type = selectedType.value

        const response = await axios.get('/api/alerts/list/', { params })
        alerts.value = response.data.items
        pagination.value = response.data.pagination
        selectedAlerts.value = []
      } catch (error) {
        console.error(error)
      }
    }

    const search = () => {
      fetchAlerts(1)
    }

    const resetFilter = () => {
      selectedStatus.value = ''
      selectedType.value = ''
      fetchAlerts(1)
    }

    const changePage = (page) => {
      fetchAlerts(page)
    }

    const toggleAll = (e) => {
      if (e.target.checked) {
        selectedAlerts.value = alerts.value.map(a => a.id)
      } else {
        selectedAlerts.value = []
      }
    }

    const acknowledge = async (id) => {
      try {
        await axios.post(`/api/alerts/${id}/acknowledge/`)
        fetchAlerts(pagination.value.page)
      } catch (error) {
        console.error(error)
      }
    }

    const resolve = async (id) => {
      try {
        await axios.post(`/api/alerts/${id}/resolve/`)
        fetchAlerts(pagination.value.page)
      } catch (error) {
        console.error(error)
      }
    }

    const bulkAcknowledge = async () => {
      if (selectedAlerts.value.length === 0) return
      try {
        await axios.post('/api/alerts/bulk/acknowledge/', { alert_ids: selectedAlerts.value })
        fetchAlerts(pagination.value.page)
      } catch (error) {
        console.error(error)
      }
    }

    const bulkResolve = async () => {
      if (selectedAlerts.value.length === 0) return
      try {
        await axios.post('/api/alerts/bulk/resolve/', { alert_ids: selectedAlerts.value })
        fetchAlerts(pagination.value.page)
      } catch (error) {
        console.error(error)
      }
    }

    const typeLabel = (type) => {
      const labels = { communication: '通信途絶', data_missing: 'データ欠損', anomaly: '異常値' }
      return labels[type] || type
    }

    const statusBadgeClass = (status) => {
      const classes = {
        open: 'am-badge am-badge-danger',
        acknowledged: 'am-badge am-badge-warning',
        resolved: 'am-badge am-badge-success'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const statusLabel = (status) => {
      const labels = { open: '未対応', acknowledged: '確認済', resolved: '解決済' }
      return labels[status] || status
    }

    onMounted(() => fetchAlerts())

    return {
      alerts,
      pagination,
      selectedStatus,
      selectedType,
      selectedAlerts,
      isAllSelected,
      search,
      resetFilter,
      changePage,
      toggleAll,
      acknowledge,
      resolve,
      bulkAcknowledge,
      bulkResolve,
      typeLabel,
      statusBadgeClass,
      statusLabel,
      formatDateTime
    }
  }
}
</script>