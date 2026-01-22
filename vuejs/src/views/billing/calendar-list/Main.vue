<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="am-h2">検針日カレンダー</h2>
      <div class="flex gap-2">
        <button class="am-btn am-btn-secondary" @click="exportCsv">CSV出力</button>
        <button class="am-btn am-btn-primary" @click="showImportModal = true">CSVインポート</button>
      </div>
    </div>

    <!-- サマリー -->
    <div class="am-card mb-6">
      <div class="am-card-header">
        <div class="am-card-title">登録状況</div>
      </div>
      <div class="am-card-body">
        <div v-if="summary.length === 0" class="am-empty">
          <div class="am-empty-title">データが登録されていません</div>
          <div class="am-empty-text">CSVインポートから検針日カレンダーを登録してください</div>
        </div>
        <table v-else class="am-table">
          <thead>
            <tr>
              <th>電力管轄</th>
              <th>年度</th>
              <th>基準検針日数</th>
              <th>レコード数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in summary" :key="`${item.zone}-${item.fiscal_year}`">
              <td>{{ item.zone_display }}</td>
              <td>{{ item.fiscal_year }}年度</td>
              <td>{{ item.base_days }}パターン</td>
              <td>{{ item.count }}件</td>
              <td>
                <button class="am-btn am-btn-ghost am-btn-sm" @click="viewDetail(item)">詳細</button>
                <button class="am-btn am-btn-danger am-btn-sm ml-2" @click="confirmDelete(item)">削除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 詳細表示 -->
    <div v-if="selectedItem" class="am-card">
      <div class="am-card-header">
        <div class="am-card-title">{{ selectedItem.zone_display }} {{ selectedItem.fiscal_year }}年度</div>
        <button class="am-btn am-btn-ghost am-btn-sm" @click="selectedItem = null">閉じる</button>
      </div>
      <div class="am-card-body">
        <div class="am-filter mb-4">
          <div class="am-filter-group">
            <label class="am-filter-label">基準検針日</label>
            <select v-model="detailFilter.base_billing_day" class="am-filter-select">
              <option value="">すべて</option>
              <option v-for="day in baseBillingDays" :key="day" :value="day">{{ day }}</option>
            </select>
          </div>
        </div>
        <table class="am-table">
          <thead>
            <tr>
              <th>基準検針日</th>
              <th>4月</th>
              <th>5月</th>
              <th>6月</th>
              <th>7月</th>
              <th>8月</th>
              <th>9月</th>
              <th>10月</th>
              <th>11月</th>
              <th>12月</th>
              <th>1月</th>
              <th>2月</th>
              <th>3月</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in detailRows" :key="item.day">
              <td class="font-medium">{{ item.day }}</td>
              <td v-for="m in fiscalMonths" :key="m">{{ formatDate(item.months[m]) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- インポートモーダル -->
    <div v-if="showImportModal" class="am-modal-overlay" @click.self="showImportModal = false">
      <div class="am-modal" style="max-width: 540px;">
        <div class="am-modal-header">
          <div class="am-modal-title">CSVインポート</div>
          <button class="am-modal-close" @click="showImportModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <!-- テンプレートダウンロード -->
          <div class="bg-gray-50 rounded-lg p-4 mb-4">
            <div class="font-medium text-gray-700 mb-3">1. テンプレートをダウンロード</div>
            <div class="flex gap-3 items-end">
              <div class="flex-1">
                <label class="am-label">電力管轄</label>
                <select v-model="templateForm.zone" class="am-select">
                  <option v-for="z in zoneOptions" :key="z.value" :value="z.value">{{ z.label }}</option>
                </select>
              </div>
              <div class="flex-1">
                <label class="am-label">年度</label>
                <select v-model="templateForm.fiscal_year" class="am-select">
                  <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}年度</option>
                </select>
              </div>
              <button class="am-btn am-btn-secondary" @click="downloadTemplate">
                テンプレート
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-2">
              ダウンロードしたCSVに実検針日(actual_billing_date)を入力してください
            </p>
          </div>
          
          <!-- ファイルアップロード -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="font-medium text-gray-700 mb-3">2. CSVファイルをアップロード</div>
            <input type="file" accept=".csv" @change="handleFileChange" class="am-input" />
          </div>

          <div v-if="importError" class="am-alert am-alert-danger mt-4">
            <div class="font-medium">インポートエラー</div>
            <ul class="text-sm mt-1 list-disc list-inside">
              <li v-for="(err, idx) in importErrors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showImportModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="importCsv" :disabled="!importFile || importing">
            {{ importing ? 'インポート中...' : 'インポート' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 削除確認モーダル -->
    <div v-if="showDeleteModal" class="am-modal-overlay" @click.self="showDeleteModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">削除確認</div>
        </div>
        <div class="am-modal-body">
          <p>{{ deleteTarget?.zone_display }} {{ deleteTarget?.fiscal_year }}年度のデータを削除しますか？</p>
          <p class="text-sm text-gray-500 mt-2">{{ deleteTarget?.count }}件のレコードが削除されます。</p>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-ghost" @click="showDeleteModal = false">キャンセル</button>
          <button class="am-btn am-btn-danger" @click="executeDelete" :disabled="deleting">
            {{ deleting ? '削除中...' : '削除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const summary = ref([])
    const selectedItem = ref(null)
    const detailData = ref([])
    const detailFilter = ref({ base_billing_day: '' })
    
    const showImportModal = ref(false)
    const importFile = ref(null)
    const importing = ref(false)
    const importError = ref(false)
    const importErrors = ref([])
    
    const showDeleteModal = ref(false)
    const deleteTarget = ref(null)
    const deleting = ref(false)

    const fiscalMonths = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
    
    // テンプレートダウンロード用
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
    
    const currentYear = new Date().getFullYear()
    const yearOptions = [currentYear, currentYear + 1, currentYear + 2]
    
    const templateForm = ref({
      zone: 3,
      fiscal_year: currentYear
    })

    // 基準検針日（東電は01-26、関電は欠番あり）
    const baseBillingDayOptions = [
      '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
      '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
      '21', '22', '23', '24', '25', '26'
    ]
    
    const baseBillingDays = computed(() => {
      const days = new Set(detailData.value.map(d => d.base_billing_day))
      return Array.from(days).sort((a, b) => parseInt(a) - parseInt(b))
    })

    // 配列として返す（数値ソート済み）
    const detailRows = computed(() => {
      const grouped = {}
      let filtered = detailData.value
      
      if (detailFilter.value.base_billing_day) {
        filtered = filtered.filter(d => d.base_billing_day === detailFilter.value.base_billing_day)
      }
      
      for (const item of filtered) {
        if (!grouped[item.base_billing_day]) {
          grouped[item.base_billing_day] = {}
        }
        grouped[item.base_billing_day][item.month] = item.actual_billing_date
      }
      
      // 配列に変換して数値ソート
      return Object.entries(grouped)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .map(([day, months]) => ({ day, months }))
    })

    const fetchSummary = async () => {
      try {
        const response = await axios.get('/api/billing/calendar/summary/')
        // zone順にソート
        summary.value = response.data.items.sort((a, b) => a.zone - b.zone || a.fiscal_year - b.fiscal_year)
      } catch (error) {
        console.error(error)
      }
    }

    const viewDetail = async (item) => {
      selectedItem.value = item
      detailFilter.value.base_billing_day = ''
      await fetchDetail()
    }

    const fetchDetail = async () => {
      if (!selectedItem.value) return
      try {
        const params = {
          zone: selectedItem.value.zone,
          fiscal_year: selectedItem.value.fiscal_year
        }
        const response = await axios.get('/api/billing/calendar/', { params })
        detailData.value = response.data.items
      } catch (error) {
        console.error(error)
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const [year, month, day] = dateStr.split('-')
      return `${parseInt(month)}/${parseInt(day)}`
    }

    const handleFileChange = (e) => {
      importFile.value = e.target.files[0]
      importError.value = false
      importErrors.value = []
    }

    const downloadTemplate = () => {
      const zone = templateForm.value.zone
      const fiscalYear = templateForm.value.fiscal_year
      
      // CSVヘッダー
      let csv = 'zone,fiscal_year,base_billing_day,month,actual_billing_date\n'
      
      // 基準検針日ごとに12ヶ月分のサンプル行を生成
      for (const baseDay of baseBillingDayOptions) {
        for (const month of fiscalMonths) {
          csv += `${zone},${fiscalYear},${baseDay},${month},\n`
        }
      }
      
      // ダウンロード
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const zoneName = zoneOptions.find(z => z.value === zone)?.label.replace('管轄', '') || 'unknown'
      link.setAttribute('download', `billing_calendar_${zoneName}_${fiscalYear}.csv`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }

    const importCsv = async () => {
      if (!importFile.value) return
      
      importing.value = true
      importError.value = false
      importErrors.value = []
      
      try {
        const formData = new FormData()
        formData.append('file', importFile.value)
        
        await axios.post('/api/billing/import/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        showImportModal.value = false
        importFile.value = null
        await fetchSummary()
        if (selectedItem.value) {
          await fetchDetail()
        }
      } catch (error) {
        importError.value = true
        importErrors.value = error.response?.data?.details || [error.response?.data?.error || 'エラーが発生しました']
      } finally {
        importing.value = false
      }
    }

    const confirmDelete = (item) => {
      deleteTarget.value = item
      showDeleteModal.value = true
    }

    const executeDelete = async () => {
      if (!deleteTarget.value) return
      
      deleting.value = true
      try {
        await axios.delete('/api/billing/delete/', {
          params: {
            zone: deleteTarget.value.zone,
            fiscal_year: deleteTarget.value.fiscal_year
          }
        })
        showDeleteModal.value = false
        if (selectedItem.value?.zone === deleteTarget.value?.zone && 
            selectedItem.value?.fiscal_year === deleteTarget.value?.fiscal_year) {
          selectedItem.value = null
          detailData.value = []
        }
        deleteTarget.value = null
        await fetchSummary()
      } catch (error) {
        console.error(error)
      } finally {
        deleting.value = false
      }
    }

    const exportCsv = async () => {
      try {
        const params = {}
        if (selectedItem.value) {
          params.zone = selectedItem.value.zone
          params.fiscal_year = selectedItem.value.fiscal_year
        }
        
        const response = await axios.get('/api/billing/export/', {
          params,
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'billing_calendar.csv')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error(error)
      }
    }

    onMounted(() => {
      fetchSummary()
    })

    return {
      summary,
      selectedItem,
      detailData,
      detailFilter,
      detailRows,
      baseBillingDays,
      fiscalMonths,
      zoneOptions,
      yearOptions,
      templateForm,
      showImportModal,
      importFile,
      importing,
      importError,
      importErrors,
      showDeleteModal,
      deleteTarget,
      deleting,
      fetchSummary,
      viewDetail,
      fetchDetail,
      formatDate,
      handleFileChange,
      downloadTemplate,
      importCsv,
      confirmDelete,
      executeDelete,
      exportCsv
    }
  }
}
</script>