<template>
  <div>
    <h2 class="text-lg font-medium mt-10">アラート一覧</h2>
    <div class="box p-5 mt-5">
      <div class="flex gap-4 mb-5">
        <select v-model="selectedStatus" class="form-select w-40">
          <option value="">全ステータス</option>
          <option value="open">未対応</option>
          <option value="acknowledged">確認済</option>
          <option value="resolved">解決済</option>
        </select>
        <select v-model="selectedType" class="form-select w-40">
          <option value="">全種別</option>
          <option value="communication">通信途絶</option>
          <option value="data_missing">データ欠損</option>
          <option value="anomaly">異常値</option>
        </select>
        <button class="btn btn-primary" @click="fetchAlerts">検索</button>
      </div>
      <table class="table table-report">
        <thead>
          <tr>
            <th>日時</th>
            <th>メーターID</th>
            <th>種別</th>
            <th>ステータス</th>
            <th>メッセージ</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in alerts" :key="alert.id">
            <td>{{ formatDate(alert.detected_at) }}</td>
            <td>{{ alert.meter_id }}</td>
            <td>{{ typeLabel(alert.alert_type) }}</td>
            <td>
              <span :class="statusClass(alert.status)">{{ statusLabel(alert.status) }}</span>
            </td>
            <td>{{ alert.message }}</td>
            <td>
              <button v-if="alert.status === 'open'" class="btn btn-sm btn-outline-primary mr-2" @click="acknowledge(alert.id)">確認</button>
              <button v-if="alert.status !== 'resolved'" class="btn btn-sm btn-outline-success" @click="resolve(alert.id)">解決</button>
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
    const alerts = ref([])
    const selectedStatus = ref('')
    const selectedType = ref('')

    const fetchAlerts = async () => {
      try {
        const params = {}
        if (selectedStatus.value) params.status = selectedStatus.value
        if (selectedType.value) params.type = selectedType.value

        const response = await axios.get('/api/alerts/list/', { params })
        alerts.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const acknowledge = async (id) => {
      try {
        await axios.post(`/api/alerts/${id}/acknowledge/`)
        fetchAlerts()
      } catch (error) {
        console.error(error)
      }
    }

    const resolve = async (id) => {
      try {
        await axios.post(`/api/alerts/${id}/resolve/`)
        fetchAlerts()
      } catch (error) {
        console.error(error)
      }
    }

    const typeLabel = (type) => {
      const labels = {
        communication: '通信途絶',
        data_missing: 'データ欠損',
        anomaly: '異常値'
      }
      return labels[type] || type
    }

    const statusClass = (status) => {
      const classes = {
        open: 'text-danger',
        acknowledged: 'text-warning',
        resolved: 'text-success'
      }
      return classes[status] || ''
    }

    const statusLabel = (status) => {
      const labels = {
        open: '未対応',
        acknowledged: '確認済',
        resolved: '解決済'
      }
      return labels[status] || status
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    onMounted(() => {
      fetchAlerts()
    })

    return {
      alerts,
      selectedStatus,
      selectedType,
      fetchAlerts,
      acknowledge,
      resolve,
      typeLabel,
      statusClass,
      statusLabel,
      formatDate
    }
  }
}
</script>