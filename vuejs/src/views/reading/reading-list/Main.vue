<template>
  <div class="p-6">
    <h2 class="am-h2 mb-6">データ一覧</h2>
    
    <div class="am-filter">
      <div class="am-filter-group">
        <label class="am-filter-label">メーター</label>
        <select v-model="selectedMeter" class="am-filter-select">
          <option value="">全メーター</option>
          <option v-for="meter in meterOptions" :key="meter.id" :value="meter.id">{{ meter.meter_id }}</option>
        </select>
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">開始日</label>
        <input type="date" v-model="startDate" class="am-filter-input" />
      </div>
      <div class="am-filter-group">
        <label class="am-filter-label">終了日</label>
        <input type="date" v-model="endDate" class="am-filter-input" />
      </div>
      <div class="am-filter-actions">
        <button class="am-btn am-btn-primary" @click="search">検索</button>
        <button class="am-btn am-btn-secondary" @click="exportCsv">CSV出力</button>
      </div>
    </div>
    
    <div class="am-card">
      <table class="am-table">
        <thead>
          <tr>
            <th>メーターID</th>
            <th>計測日時</th>
            <th>発電量(kWh)</th>
            <th>買電量(kWh)</th>
            <th>売電量(kWh)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="readings.length === 0">
            <td colspan="5">
              <div class="am-empty">
                <div class="am-empty-title">データがありません</div>
              </div>
            </td>
          </tr>
          <tr v-for="reading in readings" :key="reading.id">
            <td class="font-medium text-gray-900">{{ reading.meter_id }}</td>
            <td>{{ formatDate(reading.recorded_at) }}</td>
            <td>{{ reading.pv_energy_kwh }}</td>
            <td>{{ reading.import_kwh }}</td>
            <td>{{ reading.export_kwh }}</td>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Pagination from '@/components/Pagination.vue'

export default {
  components: { Pagination },
  setup() {
    const readings = ref([])
    const meterOptions = ref([])
    const pagination = ref({ page: 1, per_page: 20, total: 0, total_pages: 0 })
    const selectedMeter = ref('')
    const startDate = ref('')
    const endDate = ref('')

    const fetchReadings = async (page = 1) => {
      try {
        const params = { page, per_page: 20 }
        if (selectedMeter.value) params.meter_id = selectedMeter.value
        if (startDate.value) params.start_date = startDate.value
        if (endDate.value) params.end_date = endDate.value

        const response = await axios.get('/api/readings/list/', { params })
        readings.value = response.data.items
        pagination.value = response.data.pagination
      } catch (error) {
        console.error(error)
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
      fetchReadings(1)
    }

    const changePage = (page) => {
      fetchReadings(page)
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    const exportCsv = () => {
      // TODO: CSV出力
    }

    onMounted(() => {
      fetchMeterOptions()
      fetchReadings()
    })

    return {
      readings,
      meterOptions,
      pagination,
      selectedMeter,
      startDate,
      endDate,
      search,
      changePage,
      formatDate,
      exportCsv
    }
  }
}
</script>