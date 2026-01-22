<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">請求データ</h2>
      <button class="am-btn am-btn-secondary" @click="exportCsv" :disabled="!selectedGroup">
        CSVダウンロード
      </button>
    </div>

    <!-- フィルタ -->
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">年</label>
        <select v-model="filters.year" class="am-filter-select" @change="fetchGroups">
          <option value="">すべて</option>
          <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}年</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">電力管轄</label>
        <select v-model="filters.zone" class="am-filter-select" @change="fetchGroups">
          <option value="">すべて</option>
          <option v-for="z in zoneOptions" :key="z.value" :value="z.value">{{ z.label }}</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">連携状況</label>
        <select v-model="filters.fetch_status" class="am-filter-select" @change="fetchGroups">
          <option value="">すべて</option>
          <option value="pending">未処理</option>
          <option value="processing">処理中</option>
          <option value="completed">完了</option>
          <option value="error">エラー</option>
        </select>
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-ghost" @click="resetFilters">リセット</button>
        <button class="am-btn am-btn-primary" @click="fetchGroups">検索</button>
      </div>
    </div>

    <!-- グループ一覧 -->
    <div class="am-card mb-6">
      <div class="am-card-header">
        <div class="am-card-title">検針日×管轄</div>
      </div>
      <table class="am-table">
        <thead>
          <tr>
            <th>検針期間</th>
            <th>電力管轄</th>
            <th>メーター数</th>
            <th>実測合計</th>
            <th>みなし合計</th>
            <th>合計</th>
            <th>みなし件数</th>
            <th>連携状況</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="groups.length === 0">
            <td colspan="8">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr 
            v-for="g in groups" 
            :key="`${g.zone}-${g.period_end}`"
            @click="selectGroup(g)"
            class="cursor-pointer hover:bg-gray-50"
            :class="{ 'bg-blue-50': isSelected(g) }"
          >
            <td>{{ formatDate(g.period_start) }} 〜 {{ formatDate(g.period_end) }}</td>
            <td>{{ g.zone_display }}</td>
            <td>{{ g.meter_count }}</td>
            <td>{{ formatNumber(g.total_actual) }} kWh</td>
            <td>{{ formatNumber(g.total_deemed) }} kWh</td>
            <td>{{ formatNumber(g.total_kwh) }} kWh</td>
            <td>
              <span v-if="g.missing_count > 0" class="am-badge am-badge-warning">{{ g.missing_count }}件</span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td>
              <div class="flex gap-1 flex-wrap">
                <span v-if="g.completed_count > 0" class="am-badge am-badge-success text-xs">完了:{{ g.completed_count }}</span>
                <span v-if="g.pending_count > 0" class="am-badge text-xs">未処理:{{ g.pending_count }}</span>
                <span v-if="g.processing_count > 0" class="am-badge am-badge-warning text-xs">処理中:{{ g.processing_count }}</span>
                <span v-if="g.error_count > 0" class="am-badge am-badge-danger text-xs">エラー:{{ g.error_count }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="p-4 border-t" v-if="groupPagination.total_pages > 1">
        <Pagination
          :current-page="groupPagination.page"
          :total-pages="groupPagination.total_pages"
          :total="groupPagination.total"
          :per-page="groupPagination.per_page"
          @change="changeGroupPage"
        />
      </div>
    </div>

    <!-- メーター詳細 -->
    <div class="am-card" v-if="selectedGroup">
      <div class="am-card-header">
        <div class="am-card-title">
          {{ selectedGroup.zone_display }} / {{ formatDate(selectedGroup.period_end) }} のメーター詳細
        </div>
        <div class="flex gap-2 items-center">
          <input type="text" v-model="detailSearch" class="am-filter-input" placeholder="メーターID・案件名" @keyup.enter="fetchDetails" style="width: 200px;" />
          <button class="am-btn am-btn-sm am-btn-ghost" @click="fetchDetails">検索</button>
        </div>
      </div>
      <table class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>案件名</th>
            <th>実測(kWh)</th>
            <th>みなし(kWh)</th>
            <th>合計(kWh)</th>
            <th>みなし方法</th>
            <th>初回</th>
            <th>連携状況</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="details.length === 0">
            <td colspan="8">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="item in details" :key="item.id" :class="{ 'bg-yellow-50': item.deemed_method !== 'none' }">
            <td class="font-mono">{{ item.meter_id }}</td>
            <td>
              <div>{{ item.project_name || '-' }}</div>
              <div class="text-xs text-gray-500">ID: {{ item.project_id }}</div>
            </td>
            <td>{{ formatNumber(item.actual_kwh) }}</td>
            <td>{{ formatNumber(item.deemed_kwh) }}</td>
            <td>{{ formatNumber(item.total_kwh) }}</td>
            <td>
              <span v-if="item.deemed_method === 'none'" class="text-gray-400">-</span>
              <span v-else-if="item.deemed_method === 'daily'" class="am-badge am-badge-warning">6kWh/日</span>
              <span v-else-if="item.deemed_method === 'monthly'" class="am-badge am-badge-danger">180kWh/月</span>
            </td>
            <td>
              <span v-if="item.is_first_billing" class="am-badge am-badge-info">初回</span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td>
              <div class="flex flex-col gap-1">
                <span v-if="item.fetch_status === 'pending'" class="am-badge">未処理</span>
                <span v-else-if="item.fetch_status === 'processing'" class="am-badge am-badge-warning">処理中</span>
                <span v-else-if="item.fetch_status === 'completed'" class="am-badge am-badge-success">完了</span>
                <span v-else-if="item.fetch_status === 'error'" class="am-badge am-badge-danger" :title="item.fetch_error_message">エラー</span>
                <span v-else class="text-gray-400">-</span>
                <div v-if="item.fetch_status === 'error' && item.fetch_error_message" class="text-xs text-red-500 truncate max-w-32" :title="item.fetch_error_message">
                  {{ item.fetch_error_message }}
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="p-4 border-t" v-if="detailPagination.total_pages > 1">
        <Pagination
          :current-page="detailPagination.page"
          :total-pages="detailPagination.total_pages"
          :total="detailPagination.total"
          :per-page="detailPagination.per_page"
          @change="changeDetailPage"
        />
      </div>
      <div class="p-4 border-t bg-gray-50" v-if="detailTotals">
        <div class="flex justify-end gap-8 text-sm">
          <div><span class="text-gray-500">実測合計:</span> <strong>{{ formatNumber(detailTotals.actual_kwh) }} kWh</strong></div>
          <div><span class="text-gray-500">みなし合計:</span> <strong>{{ formatNumber(detailTotals.deemed_kwh) }} kWh</strong></div>
          <div><span class="text-gray-500">合計:</span> <strong>{{ formatNumber(detailTotals.total_kwh) }} kWh</strong></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import Pagination from '@/components/Pagination.vue'
import { formatDate } from '@/utils/date'

export default {
  components: { Pagination },
  setup() {
    const groups = ref([])
    const details = ref([])
    const selectedGroup = ref(null)
    const detailSearch = ref('')
    const detailTotals = ref(null)

    const filters = reactive({
      year: '',
      zone: '',
      fetch_status: ''
    })

    const groupPagination = reactive({
      page: 1,
      per_page: 20,
      total: 0,
      total_pages: 0
    })

    const detailPagination = reactive({
      page: 1,
      per_page: 20,
      total: 0,
      total_pages: 0
    })

    const currentYear = new Date().getFullYear()
    const yearOptions = [currentYear, currentYear - 1, currentYear - 2]

    const zoneOptions = [
      { value: 1, label: '北海道電力管轄' },
      { value: 2, label: '東北電力管轄' },
      { value: 3, label: '東京電力管轄' },
      { value: 4, label: '中部電力管轄' },
      { value: 5, label: '北陸電力管轄' },
      { value: 6, label: '関西電力管轄' },
      { value: 7, label: '中国電力管轄' },
      { value: 8, label: '四国電力管轄' },
      { value: 9, label: '九州電力管轄' },
      { value: 10, label: '沖縄電力管轄' },
    ]

    const fetchGroups = async () => {
      try {
        const params = { page: groupPagination.page, per_page: groupPagination.per_page }
        if (filters.year) params.year = filters.year
        if (filters.zone) params.zone = filters.zone
        if (filters.fetch_status) params.fetch_status = filters.fetch_status

        const response = await axios.get('/api/billing/summary/', { params })
        groups.value = response.data.items
        groupPagination.total = response.data.total
        groupPagination.total_pages = response.data.total_pages

        selectedGroup.value = null
        details.value = []
      } catch (error) {
        console.error(error)
      }
    }

    const resetFilters = () => {
      filters.year = ''
      filters.zone = ''
      filters.fetch_status = ''
      groupPagination.page = 1
      fetchGroups()
    }

    const changeGroupPage = (page) => {
      groupPagination.page = page
      fetchGroups()
    }

    const selectGroup = (group) => {
      selectedGroup.value = group
      detailPagination.page = 1
      detailSearch.value = ''
      fetchDetails()
    }

    const isSelected = (group) => {
      return selectedGroup.value && 
        selectedGroup.value.zone === group.zone && 
        selectedGroup.value.period_end === group.period_end
    }

    const fetchDetails = async () => {
      if (!selectedGroup.value) return

      try {
        const params = {
          zone: selectedGroup.value.zone,
          period_end: selectedGroup.value.period_end,
          page: detailPagination.page,
          per_page: detailPagination.per_page
        }
        if (detailSearch.value) params.search = detailSearch.value

        const response = await axios.get('/api/billing/summary/detail/', { params })
        details.value = response.data.items
        detailPagination.total = response.data.total
        detailPagination.total_pages = response.data.total_pages
        detailTotals.value = response.data.totals
      } catch (error) {
        console.error(error)
      }
    }

    const changeDetailPage = (page) => {
      detailPagination.page = page
      fetchDetails()
    }

    const exportCsv = async () => {
      if (!selectedGroup.value) return

      try {
        const params = {
          zone: selectedGroup.value.zone,
          period_end: selectedGroup.value.period_end
        }

        const response = await axios.get('/api/billing/summary/export/', {
          params,
          responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `billing_${selectedGroup.value.zone}_${selectedGroup.value.period_end}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error(error)
        alert('ダウンロードに失敗しました')
      }
    }

    const formatNumber = (val) => {
      if (val === null || val === undefined || val === '') return '-'
      return Number(val).toLocaleString('ja-JP', { maximumFractionDigits: 2 })
    }

    onMounted(() => {
      fetchGroups()
    })

    return {
      groups,
      details,
      selectedGroup,
      detailSearch,
      detailTotals,
      filters,
      groupPagination,
      detailPagination,
      yearOptions,
      zoneOptions,
      fetchGroups,
      resetFilters,
      changeGroupPage,
      selectGroup,
      isSelected,
      fetchDetails,
      changeDetailPage,
      exportCsv,
      formatDate,
      formatNumber
    }
  }
}
</script>