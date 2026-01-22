<template>
  <div class="p-6">
    <h2 class="am-h2 mb-6">データ一覧</h2>
    
    <!-- タブ -->
    <div class="am-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        @click="currentTab = tab.value"
        :class="['am-tab', { 'am-tab-active': currentTab === tab.value }]"
      >
        {{ tab.label }}
      </button>
    </div>
    
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">メーター</label>
        <select v-model="selectedMeter" class="am-filter-select">
          <option value="">全メーター</option>
          <option v-for="meter in meterOptions" :key="meter.id" :value="meter.id">{{ meter.meter_id }}</option>
        </select>
      </div>
      <div class="am-filter-group" v-if="currentTab !== 'monthly'">
        <label class="am-filter-label">開始日</label>
        <input type="date" v-model="startDate" class="am-filter-input" />
      </div>
      <div class="am-filter-group" v-if="currentTab !== 'monthly'">
        <label class="am-filter-label">終了日</label>
        <input type="date" v-model="endDate" class="am-filter-input" />
      </div>
      <div class="am-filter-group" v-if="currentTab === 'monthly'">
        <label class="am-filter-label">年</label>
        <select v-model="selectedYear" class="am-filter-select">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}年</option>
        </select>
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-ghost" @click="resetFilter">リセット</button>
        <button class="am-btn am-btn-primary" @click="search">検索</button>
        <button class="am-btn am-btn-secondary" @click="showExportModal = true">CSV出力</button>
      </div>
    </div>

    <!-- 日次グラフ -->
    <div class="am-card mb-4" v-if="currentTab === 'daily' && chartItems.length > 0">
      <div class="am-card-header">
        <div class="am-card-title">日別推移</div>
      </div>
      <div class="am-card-body">
        <div class="h-64">
          <Bar :data="dailyChartData" :options="chartOptions" />
        </div>
      </div>
    </div>

    <!-- 月次グラフ -->
    <div class="am-card mb-4" v-if="currentTab === 'monthly' && chartItems.length > 0">
      <div class="am-card-header">
        <div class="am-card-title">月別推移</div>
      </div>
      <div class="am-card-body">
        <div class="h-64">
          <Bar :data="monthlyChartData" :options="chartOptions" />
        </div>
      </div>
    </div>
    
    <div class="am-card">
      <!-- 30分データ -->
      <table v-if="currentTab === 'readings'" class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>計測日時</th>
            <th>発電量(kWh)</th>
            <th>逆潮流(kWh)</th>
            <th>買電(kWh)</th>
            <th>売電(kWh)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="6">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.id">
            <td class="font-medium text-gray-900">{{ item.meter_id }}</td>
            <td>{{ formatDateTime(item.timestamp) }}</td>
            <td>{{ formatNumber(item.import_kwh) }}</td>
            <td>{{ formatNumber(item.export_kwh) }}</td>
            <td>{{ formatNumber(item.route_b_import_kwh) }}</td>
            <td>{{ formatNumber(item.route_b_export_kwh) }}</td>
          </tr>
        </tbody>
      </table>

      <!-- 日次集計 -->
      <table v-if="currentTab === 'daily'" class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>日付</th>
            <th>発電量(kWh)</th>
            <th>売電量(kWh)</th>
            <th>自家消費量(kWh)</th>
            <th>買電量(kWh)</th>
            <th>レコード数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="7">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.id">
            <td class="font-medium text-gray-900">{{ item.meter_id }}</td>
            <td>{{ formatDateFromISO(item.date) }}</td>
            <td>{{ formatNumber(item.generation_kwh) }}</td>
            <td>{{ formatNumber(item.export_kwh) }}</td>
            <td>{{ formatNumber(item.self_consumption_kwh) }}</td>
            <td>{{ formatNumber(item.grid_import_kwh) }}</td>
            <td>{{ item.record_count }}</td>
          </tr>
        </tbody>
      </table>

      <!-- 月次集計 -->
      <table v-if="currentTab === 'monthly'" class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>年月</th>
            <th>発電量(kWh)</th>
            <th>売電量(kWh)</th>
            <th>自家消費量(kWh)</th>
            <th>買電量(kWh)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="6">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="item in items" :key="item.id">
            <td class="font-medium text-gray-900">{{ item.meter_id }}</td>
            <td>{{ formatYearMonthFromString(item.year_month) }}</td>
            <td>{{ formatNumber(item.generation_kwh) }}</td>
            <td>{{ formatNumber(item.export_kwh) }}</td>
            <td>{{ formatNumber(item.self_consumption_kwh) }}</td>
            <td>{{ formatNumber(item.grid_import_kwh) }}</td>
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

    <!-- CSV出力モーダル -->
    <div v-if="showExportModal" class="am-modal-overlay" @click.self="showExportModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">CSV出力</div>
          <button class="am-modal-close" @click="showExportModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">データ種別</label>
            <select v-model="exportForm.type" class="am-select">
              <option value="readings">30分データ</option>
              <option value="daily">日次集計</option>
              <option value="monthly">月次集計</option>
            </select>
          </div>
          
          <div class="am-form-group">
            <label class="am-label">メーター</label>
            <select v-model="exportForm.meter_id" class="am-select">
              <option value="">全メーター</option>
              <option v-for="meter in meterOptions" :key="meter.id" :value="meter.id">{{ meter.meter_id }}</option>
            </select>
          </div>

          <!-- 30分データ: 日選択 -->
          <div v-if="exportForm.type === 'readings'" class="am-form-group">
            <label class="am-label">対象日 <span class="text-red-500">*</span></label>
            <input type="date" v-model="exportForm.date" class="am-input" />
            <div class="am-form-hint">30分データは1日単位でダウンロードできます</div>
          </div>

          <!-- 日次集計: 月選択 -->
          <div v-if="exportForm.type === 'daily'" class="am-form-group">
            <label class="am-label">対象月 <span class="text-red-500">*</span></label>
            <input type="month" v-model="exportForm.month" class="am-input" />
            <div class="am-form-hint">日次集計は1ヶ月単位でダウンロードできます</div>
          </div>

          <!-- 月次集計: 年選択 -->
          <div v-if="exportForm.type === 'monthly'" class="am-form-group">
            <label class="am-label">対象年 <span class="text-red-500">*</span></label>
            <select v-model="exportForm.year" class="am-select">
              <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}年</option>
            </select>
            <div class="am-form-hint">月次集計は1年単位でダウンロードできます</div>
          </div>

          <div v-if="exportError" class="am-alert am-alert-danger">
            {{ exportError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showExportModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="exportCsv" :disabled="exporting">
            {{ exporting ? 'ダウンロード中...' : 'ダウンロード' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue'
import axios from 'axios'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import Pagination from '@/components/Pagination.vue'
import { formatDateTime } from '@/utils/date'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default {
  components: { Pagination, Bar },
  setup() {
    const tabs = [
      { value: 'readings', label: '30分データ' },
      { value: 'daily', label: '日次集計' },
      { value: 'monthly', label: '月次集計' }
    ]
    const currentTab = ref('readings')
    const items = ref([])
    const chartItems = ref([])
    const meterOptions = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const selectedMeter = ref('')
    const startDate = ref('')
    const endDate = ref('')
    const selectedYear = ref(new Date().getFullYear())

    // CSV出力モーダル
    const showExportModal = ref(false)
    const exporting = ref(false)
    const exportError = ref('')
    const today = new Date().toISOString().slice(0, 10)
    const currentMonth = new Date().toISOString().slice(0, 7)
    const exportForm = ref({
      type: 'readings',
      meter_id: '',
      date: today,
      month: currentMonth,
      year: new Date().getFullYear()
    })

    const yearOptions = computed(() => {
      const currentYear = new Date().getFullYear()
      return Array.from({ length: 5 }, (_, i) => currentYear - i)
    })

    // グラフデータ（日次）
    const dailyChartData = computed(() => {
      const data = chartItems.value
      
      const labels = data.map(item => {
        const d = new Date(item.date)
        return `${d.getMonth() + 1}/${d.getDate()}`
      })

      return {
        labels,
        datasets: [
          {
            label: '発電量',
            data: data.map(item => Number(item.generation_kwh) || 0),
            backgroundColor: 'rgba(233, 30, 140, 0.85)',
            borderRadius: 4,
          },
          {
            label: '自家消費',
            data: data.map(item => Number(item.self_consumption_kwh) || 0),
            backgroundColor: 'rgba(124, 77, 255, 0.85)',
            borderRadius: 4,
          },
          {
            label: '売電',
            data: data.map(item => Number(item.export_kwh) || 0),
            backgroundColor: 'rgba(156, 163, 175, 0.85)',
            borderRadius: 4,
          }
        ]
      }
    })

    // グラフデータ（月次）
    const monthlyChartData = computed(() => {
      const data = chartItems.value
      
      const labels = data.map(item => item.year_month)

      return {
        labels,
        datasets: [
          {
            label: '発電量',
            data: data.map(item => Number(item.generation_kwh) || 0),
            backgroundColor: 'rgba(233, 30, 140, 0.85)',
            borderRadius: 4,
          },
          {
            label: '自家消費',
            data: data.map(item => Number(item.self_consumption_kwh) || 0),
            backgroundColor: 'rgba(124, 77, 255, 0.85)',
            borderRadius: 4,
          },
          {
            label: '売電',
            data: data.map(item => Number(item.export_kwh) || 0),
            backgroundColor: 'rgba(156, 163, 175, 0.85)',
            borderRadius: 4,
          }
        ]
      }
    })

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        }
      },
      scales: {
        x: {
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0, 0, 0, 0.05)' },
          title: { display: true, text: 'kWh' }
        }
      }
    }

    const apiEndpoints = {
      readings: '/api/readings/list/',
      daily: '/api/readings/daily/list/',
      monthly: '/api/readings/monthly/list/'
    }

    const chartEndpoints = {
      daily: '/api/readings/daily/chart/',
      monthly: '/api/readings/monthly/chart/'
    }

    const exportEndpoints = {
      readings: '/api/readings/export/',
      daily: '/api/readings/daily/export/',
      monthly: '/api/readings/monthly/export/'
    }

    const fetchData = async (page = 1) => {
      try {
        const params = { page, per_page: 20 }
        if (selectedMeter.value) params.meter_id = selectedMeter.value
        
        if (currentTab.value === 'monthly') {
          params.year = selectedYear.value
        } else {
          if (startDate.value) params.start_date = startDate.value
          if (endDate.value) params.end_date = endDate.value
        }

        const response = await axios.get(apiEndpoints[currentTab.value], { params })
        items.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
      }
    }

    const fetchChartData = async () => {
      if (currentTab.value === 'readings') {
        chartItems.value = []
        return
      }

      try {
        const params = {}
        if (selectedMeter.value) {
          params.meter_id = selectedMeter.value
        }
        
        if (currentTab.value === 'daily') {
          params.days = 30
        } else {
          params.months = 12
        }

        const response = await axios.get(chartEndpoints[currentTab.value], { params })
        chartItems.value = response.data.items
      } catch (error) {
        console.error(error)
        chartItems.value = []
      }
    }

    const fetchMeterOptions = async () => {
      try {
        const response = await axios.get('/api/meters/list/', { params: { per_page: 1000 } })
        meterOptions.value = response.data.items
      } catch (error) {
        console.error(error)
      }
    }

    const search = () => {
      fetchData(1)
      fetchChartData()
    }

    const resetFilter = () => {
      selectedMeter.value = ''
      startDate.value = ''
      endDate.value = ''
      selectedYear.value = new Date().getFullYear()
      fetchData(1)
      fetchChartData()
    }

    const changePage = (page) => {
      fetchData(page)
    }

    const formatDateFromISO = (dateStr) => {
      if (!dateStr) return '-'
      const [year, month, day] = dateStr.split('-')
      return `${year}年${month}月${day}日`
    }

    const formatYearMonthFromString = (yearMonthStr) => {
      if (!yearMonthStr) return '-'
      const [year, month] = yearMonthStr.split('-')
      return `${year}年${month}月`
    }

    const formatNumber = (num) => {
      if (num === null || num === undefined) return '-'
      return Number(num).toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const exportCsv = async () => {
      exportError.value = ''
      
      if (exportForm.value.type === 'readings' && !exportForm.value.date) {
        exportError.value = '対象日を選択してください'
        return
      }
      if (exportForm.value.type === 'daily' && !exportForm.value.month) {
        exportError.value = '対象月を選択してください'
        return
      }

      exporting.value = true
      
      try {
        const params = {}
        if (exportForm.value.meter_id) {
          params.meter_id = exportForm.value.meter_id
        }
        
        if (exportForm.value.type === 'readings') {
          params.start_date = exportForm.value.date
          params.end_date = exportForm.value.date
        } else if (exportForm.value.type === 'daily') {
          const [year, month] = exportForm.value.month.split('-')
          const lastDay = new Date(year, month, 0).getDate()
          params.start_date = `${exportForm.value.month}-01`
          params.end_date = `${exportForm.value.month}-${String(lastDay).padStart(2, '0')}`
        } else {
          params.year = exportForm.value.year
        }
        
        const response = await axios.get(exportEndpoints[exportForm.value.type], {
          params,
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        let dateSuffix = ''
        if (exportForm.value.type === 'readings') {
          dateSuffix = exportForm.value.date.replace(/-/g, '')
        } else if (exportForm.value.type === 'daily') {
          dateSuffix = exportForm.value.month.replace('-', '')
        } else {
          dateSuffix = String(exportForm.value.year)
        }
        
        const meterSuffix = exportForm.value.meter_id 
          ? meterOptions.value.find(m => m.id === exportForm.value.meter_id)?.meter_id || 'unknown'
          : 'all'
        
        link.setAttribute('download', `${exportForm.value.type}_${meterSuffix}_${dateSuffix}.csv`)
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        showExportModal.value = false
      } catch (error) {
        console.error(error)
        exportError.value = 'ダウンロードに失敗しました'
      } finally {
        exporting.value = false
      }
    }

    watch(currentTab, () => {
      items.value = []
      chartItems.value = []
      pagination.value = { page: 1, per_page: 20, total: 0, total_pages: 0 }
      fetchData(1)
      fetchChartData()
    })

    watch(showExportModal, (val) => {
      if (val) {
        exportForm.value.type = currentTab.value
        exportError.value = ''
      }
    })

    onMounted(() => {
      fetchMeterOptions()
      fetchData()
      fetchChartData()
    })

    return {
      tabs,
      currentTab,
      items,
      chartItems,
      meterOptions,
      pagination,
      selectedMeter,
      startDate,
      endDate,
      selectedYear,
      yearOptions,
      dailyChartData,
      monthlyChartData,
      chartOptions,
      showExportModal,
      exporting,
      exportError,
      exportForm,
      search,
      resetFilter,
      changePage,
      formatDateTime,
      formatDateFromISO,
      formatYearMonthFromString,
      formatNumber,
      exportCsv
    }
  }
}
</script>