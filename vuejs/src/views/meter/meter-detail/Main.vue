<template>
  <div>
    <h2 class="text-lg font-medium mt-10">メーター詳細</h2>
    <div class="box p-5 mt-5" v-if="meter">
      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 lg:col-span-6">
          <h3 class="font-medium mb-3">基本情報</h3>
          <table class="table">
            <tr>
              <th class="w-40">メーターID</th>
              <td>{{ meter.meter_id }}</td>
            </tr>
            <tr>
              <th>ステータス</th>
              <td>{{ statusLabel(meter.status) }}</td>
            </tr>
            <tr>
              <th>登録日</th>
              <td>{{ formatDate(meter.registered_at) }}</td>
            </tr>
            <tr>
              <th>最終受信</th>
              <td>{{ formatDate(meter.last_received_at) }}</td>
            </tr>
          </table>
        </div>
        <div class="col-span-12 lg:col-span-6">
          <h3 class="font-medium mb-3">案件紐付け</h3>
          <p v-if="meter.current_project_id">案件ID: {{ meter.current_project_id }}</p>
          <p v-else>未割当</p>
          <button class="btn btn-outline-primary mt-3" @click="showAssignModal = true">案件変更</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const route = useRoute()
    const meter = ref(null)
    const showAssignModal = ref(false)

    const fetchMeter = async () => {
      try {
        const response = await axios.get(`/api/meters/${route.params.pk}/detail/`)
        meter.value = response.data
      } catch (error) {
        console.error(error)
      }
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
      fetchMeter()
    })

    return {
      meter,
      showAssignModal,
      statusLabel,
      formatDate
    }
  }
}
</script>