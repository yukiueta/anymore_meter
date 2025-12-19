<template>
  <div>
    <h2 class="text-lg font-medium mt-10">メーター一覧</h2>
    <div class="box p-5 mt-5">
      <div class="flex justify-end mb-5">
        <button class="btn btn-primary" @click="showCreateModal = true">新規登録</button>
      </div>
      <table class="table table-report">
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
          <tr v-for="meter in meters" :key="meter.id">
            <td>{{ meter.meter_id }}</td>
            <td>
              <span :class="statusClass(meter.status)">{{ statusLabel(meter.status) }}</span>
            </td>
            <td>{{ meter.project_name || '未割当' }}</td>
            <td>{{ formatDate(meter.last_received_at) }}</td>
            <td>
              <router-link :to="`/meter/detail/${meter.id}`" class="btn btn-sm btn-outline-primary">詳細</router-link>
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
    const meters = ref([])
    const showCreateModal = ref(false)

    const fetchMeters = async () => {
      try {
        const response = await axios.get('/api/meters/list/')
        meters.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const statusClass = (status) => {
      const classes = {
        active: 'text-success',
        inactive: 'text-warning',
        offline: 'text-danger',
        registered: 'text-slate-500'
      }
      return classes[status] || ''
    }

    const statusLabel = (status) => {
      const labels = {
        active: '稼働中',
        inactive: '停止中',
        offline: 'オフライン',
        registered: '登録済み'
      }
      return labels[status] || status
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    onMounted(() => {
      fetchMeters()
    })

    return {
      meters,
      showCreateModal,
      statusClass,
      statusLabel,
      formatDate
    }
  }
}
</script>