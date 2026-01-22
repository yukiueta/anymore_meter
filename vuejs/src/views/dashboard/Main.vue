<template>
  <div class="p-6">
    <h2 class="am-h2 mb-6">ダッシュボード</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      <div class="am-card">
        <div class="am-card-body">
          <div class="am-text-sm mb-2">全メーター数</div>
          <div class="am-h1">{{ stats.total_meters }}</div>
        </div>
      </div>
      
      <div class="am-card">
        <div class="am-card-body">
          <div class="am-text-sm mb-2">稼働中</div>
          <div class="am-h1 text-green-600">{{ stats.active_meters }}</div>
        </div>
      </div>
      
      <div class="am-card">
        <div class="am-card-body">
          <div class="am-text-sm mb-2">オフライン</div>
          <div class="am-h1" :class="stats.offline_meters > 0 ? 'text-orange-600' : ''">{{ stats.offline_meters }}</div>
        </div>
      </div>
      
      <div class="am-card">
        <div class="am-card-body">
          <div class="am-text-sm mb-2">本日の受信件数</div>
          <div class="am-h1">{{ stats.today_readings }}</div>
        </div>
      </div>
      
      <div class="am-card">
        <div class="am-card-body">
          <div class="am-text-sm mb-2">未対応アラート</div>
          <div class="am-h1" :class="stats.open_alerts > 0 ? 'text-red-600' : ''">{{ stats.open_alerts }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const stats = ref({
      total_meters: 0,
      active_meters: 0,
      offline_meters: 0,
      today_readings: 0,
      open_alerts: 0
    })

    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/meters/dashboard/stats/')
        stats.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    onMounted(() => {
      fetchStats()
    })

    return {
      stats
    }
  }
}
</script>