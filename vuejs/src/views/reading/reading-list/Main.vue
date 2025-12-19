<template>
  <div>
    <h2 class="text-lg font-medium mt-10">データ一覧</h2>
    <div class="box p-5 mt-5">
      <div class="flex gap-4 mb-5">
        <select v-model="selectedMeter" class="form-select w-48">
          <option value="">全メーター</option>
          <option v-for="meter in meters" :key="meter.id" :value="meter.id">{{ meter.meter_id }}</option>
        </select>
        <input type="date" v-model="startDate" class="form-control w-40" />
        <input type="date" v-model="endDate" class="form-control w-40" />
        <button class="btn btn-primary" @click="fetchReadings">検索</button>
        <button class="btn btn-outline-secondary" @click="exportCsv">CSV出力</button>
      </div>
      <table class="table table-report">
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
          <tr v-for="reading in readings" :key="reading.id">
            <td>{{ reading.meter_id }}</td>
            <td>{{ formatDate(reading.recorded_at) }}</td>
            <td>{{ reading.pv_energy_kwh }}</td>
            <td>{{ reading.import_kwh }}</td>
            <td>{{ reading.export_kwh }}</td>
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
    const readings = ref([])
    const meters = ref([])
    const selectedMeter = ref('')
    const startDate = ref('')
    const endDate = ref('')

    const fetchReadings = async () => {
      try {
        const params = {}
        if (selectedMeter.value) params.meter_id = selectedMeter.value
        if (startDate.value) params.start_date = startDate.value
        if (endDate.value) params.end_date = endDate.value

        const response = await axios.get('/api/readings/list/', { params })
        readings.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const fetchMeters = async () => {
      try {
        const response = await axios.get('/api/meters/list/')
        meters.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('ja-JP')
    }

    const exportCsv = () => {
      // TODO: CSV出力
    }

    onMounted(() => {
      fetchMeters()
      fetchReadings()
    })

    return {
      readings,
      meters,
      selectedMeter,
      startDate,
      endDate,
      fetchReadings,
      formatDate,
      exportCsv
    }
  }
}
</script>