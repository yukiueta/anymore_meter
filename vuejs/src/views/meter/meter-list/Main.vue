<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">メーター一覧</h2>
      <div class="flex gap-2">
        <button class="am-btn am-btn-secondary" @click="showBulkModal = true">
          一括登録
        </button>
        <button class="am-btn am-btn-primary" @click="showCreateModal = true">
          + 新規登録
        </button>
      </div>
    </div>
    
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">ステータス</label>
        <select v-model="selectedStatus" class="am-filter-select">
          <option value="">全ステータス</option>
          <option value="inactive">未稼働</option>
          <option value="pending">登録待ち</option>
          <option value="active">稼働中</option>
          <option value="error">エラー</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">セットアップ</label>
        <select v-model="selectedSetupStatus" class="am-filter-select">
          <option value="">すべて</option>
          <option value="unlinked">未割当</option>
          <option value="zone_missing">管轄未設定</option>
          <option value="billing_day_missing">検針日未設定</option>
          <option value="complete">完了</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">検索</label>
        <input type="text" v-model="searchQuery" class="am-filter-input" placeholder="メーターID" />
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-ghost" @click="resetFilter">リセット</button>
        <button class="am-btn am-btn-primary" @click="search">検索</button>
        <button class="am-btn am-btn-secondary" @click="exportCsv">CSV出力</button>
      </div>
    </div>
    
    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>ステータス</th>
            <th>セットアップ</th>
            <th>紐付け案件</th>
            <th>電力管轄</th>
            <th>最終受信</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="meters.length === 0">
            <td colspan="7">
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
            <td>
              <span :class="setupBadgeClass(meter.setup_status)">
                {{ setupLabel(meter.setup_status) }}
              </span>
            </td>
            <td>{{ meter.current_project_name || meter.current_project_id || '未割当' }}</td>
            <td>{{ meter.current_zone_display || '-' }}</td>
            <td>{{ formatDateTime(meter.last_received_at) }}</td>
            <td>
              <div class="flex gap-2">
                <router-link :to="`/meter/detail/${meter.id}`" class="am-btn am-btn-sm am-btn-secondary">詳細</router-link>
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
            <input type="text" v-model="newMeter.meter_id" class="am-input" placeholder="J220004683" />
          </div>
          <div class="am-form-group">
            <label class="am-label">ステータス</label>
            <select v-model="newMeter.status" class="am-select">
              <option value="inactive">未稼働</option>
              <option value="pending">登録待ち</option>
              <option value="active">稼働中</option>
            </select>
          </div>
          <div class="am-form-group">
            <label class="am-label">設置日</label>
            <input type="date" v-model="newMeter.installed_at" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-checkbox">
              <input type="checkbox" v-model="newMeter.b_route_enabled" />
              <span>Bルート有効</span>
            </label>
          </div>
          <div v-if="newMeter.b_route_enabled">
            <div class="am-form-group">
              <label class="am-label">BルートID</label>
              <input type="text" v-model="newMeter.b_route_id" class="am-input" placeholder="BルートID" />
            </div>
            <div class="am-form-group">
              <label class="am-label">Bルートパスワード</label>
              <input type="text" v-model="newMeter.b_route_password" class="am-input" placeholder="パスワード" />
            </div>
          </div>
          <div v-if="createError" class="am-alert am-alert-danger">
            {{ createError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showCreateModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="createMeter" :disabled="creating">
            {{ creating ? '登録中...' : '登録' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 一括登録モーダル -->
    <div v-if="showBulkModal" class="am-modal-overlay" @click.self="showBulkModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">メーター一括登録</div>
          <button class="am-modal-close" @click="showBulkModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">メーターID（1行に1つ）</label>
            <textarea v-model="bulkMeterIds" class="am-textarea" rows="10" placeholder="J220004683&#10;J220004684&#10;J220004685"></textarea>
          </div>
          <div v-if="bulkResult" class="am-alert" :class="bulkResult.errors.length > 0 ? 'am-alert-warning' : 'am-alert-success'">
            {{ bulkResult.created }}件登録しました
            <div v-if="bulkResult.errors.length > 0" class="mt-2 text-sm">
              エラー: {{ bulkResult.errors.map(e => e.meter_id).join(', ') }}
            </div>
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showBulkModal = false">閉じる</button>
          <button class="am-btn am-btn-primary" @click="bulkCreate" :disabled="bulkCreating">
            {{ bulkCreating ? '登録中...' : '一括登録' }}
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
    const meters = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const showCreateModal = ref(false)
    const showBulkModal = ref(false)
    const creating = ref(false)
    const bulkCreating = ref(false)
    const createError = ref('')
    const bulkResult = ref(null)
    const bulkMeterIds = ref('')
    const selectedStatus = ref('')
    const selectedSetupStatus = ref('')
    const searchQuery = ref('')
    const newMeter = ref({
      meter_id: '',
      status: 'inactive',
      installed_at: '',
      b_route_enabled: true,
      b_route_id: '',
      b_route_password: ''
    })

    const fetchMeters = async (page = 1) => {
      try {
        const params = { page, per_page: 20 }
        if (selectedStatus.value) params.status = selectedStatus.value
        if (selectedSetupStatus.value) params.setup_status = selectedSetupStatus.value
        if (searchQuery.value) params.search = searchQuery.value
        
        const response = await axios.get('/api/meters/list/', { params })
        meters.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
      }
    }

    const search = () => {
      fetchMeters(1)
    }

    const resetFilter = () => {
      selectedStatus.value = ''
      selectedSetupStatus.value = ''
      searchQuery.value = ''
      fetchMeters(1)
    }

    const exportCsv = async () => {
      try {
        const params = {}
        if (selectedStatus.value) params.status = selectedStatus.value
        if (searchQuery.value) params.search = searchQuery.value
        
        const response = await axios.get('/api/meters/export/', {
          params,
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const date = new Date().toISOString().slice(0, 10).replace(/-/g, '')
        link.setAttribute('download', `meters_${date}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error(error)
        alert('CSV出力に失敗しました')
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
        newMeter.value = {
          meter_id: '',
          status: 'inactive',
          installed_at: '',
          b_route_enabled: true,
          b_route_id: '',
          b_route_password: ''
        }
        fetchMeters(1)
      } catch (error) {
        createError.value = error.response?.data?.error || '登録に失敗しました'
      } finally {
        creating.value = false
      }
    }

    const bulkCreate = async () => {
      const ids = bulkMeterIds.value.split('\n').map(id => id.trim()).filter(id => id)
      if (ids.length === 0) return
      
      bulkCreating.value = true
      bulkResult.value = null
      try {
        const response = await axios.post('/api/meters/bulk/create/', {
          meters: ids.map(meter_id => ({ meter_id, status: 'inactive', b_route_enabled: true }))
        })
        bulkResult.value = response.data
        fetchMeters(1)
      } catch (error) {
        console.error(error)
      } finally {
        bulkCreating.value = false
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
        pending: 'am-badge am-badge-warning',
        inactive: 'am-badge am-badge-gray',
        error: 'am-badge am-badge-danger'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const statusLabel = (status) => {
      const labels = {
        active: '稼働中',
        pending: '登録待ち',
        inactive: '未稼働',
        error: 'エラー'
      }
      return labels[status] || status
    }

    const setupBadgeClass = (status) => {
      const classes = {
        complete: 'am-badge am-badge-success',
        unlinked: 'am-badge am-badge-gray',
        zone_missing: 'am-badge am-badge-warning',
        billing_day_missing: 'am-badge am-badge-warning'
      }
      return classes[status] || 'am-badge am-badge-gray'
    }

    const setupLabel = (status) => {
      const labels = {
        complete: '完了',
        unlinked: '未割当',
        zone_missing: '管轄未設定',
        billing_day_missing: '検針日未設定'
      }
      return labels[status] || status
    }

    onMounted(() => fetchMeters())

    return {
      meters, pagination, showCreateModal, showBulkModal, creating, bulkCreating,
      createError, bulkResult, bulkMeterIds, selectedStatus, selectedSetupStatus, searchQuery, newMeter,
      search, resetFilter, exportCsv, changePage, createMeter, bulkCreate, deleteMeter,
      statusBadgeClass, statusLabel, setupBadgeClass, setupLabel, formatDateTime
    }
  }
}
</script>