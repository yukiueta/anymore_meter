<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="am-h2">メーター詳細</h2>
      <router-link to="/meter/list" class="am-btn am-btn-secondary">
        ← 一覧に戻る
      </router-link>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6" v-if="meter">
      <div class="am-card">
        <div class="am-card-header">
          <div class="am-card-title">基本情報</div>
        </div>
        <div class="am-card-body">
          <dl class="space-y-4">
            <div class="flex">
              <dt class="am-label w-32">メーターID</dt>
              <dd class="am-text font-medium text-gray-900">{{ meter.meter_id }}</dd>
            </div>
            <div class="flex">
              <dt class="am-label w-32">ステータス</dt>
              <dd>
                <span :class="statusBadgeClass(meter.status)">{{ statusLabel(meter.status) }}</span>
              </dd>
            </div>
            <div class="flex">
              <dt class="am-label w-32">登録日</dt>
              <dd class="am-text">{{ formatDate(meter.registered_at) }}</dd>
            </div>
            <div class="flex">
              <dt class="am-label w-32">最終受信</dt>
              <dd class="am-text">{{ formatDate(meter.last_received_at) }}</dd>
            </div>
          </dl>
        </div>
        <div class="am-card-footer">
          <div class="flex gap-2">
            <button class="am-btn am-btn-primary" @click="openEditModal">編集</button>
            <button class="am-btn am-btn-danger" @click="deleteMeter">削除</button>
          </div>
        </div>
      </div>
      
      <div class="am-card">
        <div class="am-card-header">
          <div class="am-card-title">案件紐付け</div>
        </div>
        <div class="am-card-body">
          <p v-if="meter.current_project_id" class="am-text mb-4">
            案件ID: {{ meter.current_project_id }}
          </p>
          <p v-else class="am-text mb-4 text-gray-400">未割当</p>
          <button class="am-btn am-btn-outline" @click="showAssignModal = true">
            案件変更
          </button>
        </div>
      </div>
    </div>

    <!-- 編集モーダル -->
    <div v-if="showEditModal" class="am-modal-overlay" @click.self="showEditModal = false">
      <div class="am-modal">
        <div class="am-modal-header">
          <div class="am-modal-title">メーター編集</div>
          <button class="am-modal-close" @click="showEditModal = false">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="am-modal-body">
          <div class="am-form-group">
            <label class="am-label">メーターID</label>
            <input type="text" v-model="editForm.meter_id" class="am-input" />
          </div>
          <div class="am-form-group">
            <label class="am-label">ステータス</label>
            <select v-model="editForm.status" class="am-select">
              <option value="registered">登録済み</option>
              <option value="active">稼働中</option>
              <option value="inactive">停止中</option>
              <option value="offline">オフライン</option>
            </select>
          </div>
          <div v-if="editError" class="am-alert am-alert-danger">
            {{ editError }}
          </div>
        </div>
        <div class="am-modal-footer">
          <button class="am-btn am-btn-secondary" @click="showEditModal = false">キャンセル</button>
          <button class="am-btn am-btn-primary" @click="updateMeter" :disabled="updating">
            {{ updating ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

export default {
  setup() {
    const route = useRoute()
    const router = useRouter()
    const meter = ref(null)
    const showAssignModal = ref(false)
    const showEditModal = ref(false)
    const updating = ref(false)
    const editError = ref('')
    const editForm = ref({
      meter_id: '',
      status: 'registered'
    })

    const fetchMeter = async () => {
      try {
        const response = await axios.get(`/api/meters/${route.params.pk}/detail/`)
        meter.value = response.data
      } catch (error) {
        console.error(error)
      }
    }

    const openEditModal = () => {
      editForm.value = {
        meter_id: meter.value.meter_id,
        status: meter.value.status
      }
      editError.value = ''
      showEditModal.value = true
    }

    const updateMeter = async () => {
      updating.value = true
      editError.value = ''
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/update/`, editForm.value)
        showEditModal.value = false
        fetchMeter()
      } catch (error) {
        editError.value = error.response?.data?.message || '更新に失敗しました'
      } finally {
        updating.value = false
      }
    }

    const deleteMeter = async () => {
      if (!confirm(`${meter.value.meter_id}を削除しますか?`)) return
      
      try {
        await axios.post(`/api/meters/${route.params.pk}/delete/`)
        router.push('/meter/list')
      } catch (error) {
        alert('削除に失敗しました')
      }
    }

    const statusBadgeClass = (status) => {
      const classes = {
        active: 'am-badge am-badge-success',
        inactive: 'am-badge am-badge-warning',
        offline: 'am-badge am-badge-danger',
        registered: 'am-badge am-badge-gray'
      }
      return classes[status] || 'am-badge am-badge-gray'
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
      showEditModal,
      updating,
      editError,
      editForm,
      openEditModal,
      updateMeter,
      deleteMeter,
      statusBadgeClass,
      statusLabel,
      formatDate
    }
  }
}
</script>