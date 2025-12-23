<template>
  <div class="am-pagination" v-if="totalPages >= 1">
    <button 
      class="am-pagination-item" 
      :disabled="currentPage === 1"
      @click="$emit('change', currentPage - 1)"
    >
      ←
    </button>
    
    <template v-for="page in displayPages" :key="page">
      <span v-if="page === '...'" class="am-pagination-ellipsis">...</span>
      <button 
        v-else
        class="am-pagination-item" 
        :class="{ 'am-pagination-active': page === currentPage }"
        @click="$emit('change', page)"
      >
        {{ page }}
      </button>
    </template>
    
    <button 
      class="am-pagination-item" 
      :disabled="currentPage === totalPages"
      @click="$emit('change', currentPage + 1)"
    >
      →
    </button>
    
    <span class="am-pagination-info">
      {{ total }}件中 {{ startItem }}-{{ endItem }}件
    </span>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  props: {
    currentPage: { type: Number, required: true },
    totalPages: { type: Number, required: true },
    total: { type: Number, required: true },
    perPage: { type: Number, default: 20 }
  },
  emits: ['change'],
  setup(props) {
    const displayPages = computed(() => {
      const pages = []
      const current = props.currentPage
      const total = props.totalPages
      
      if (total <= 7) {
        for (let i = 1; i <= total; i++) pages.push(i)
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) pages.push(i)
          pages.push('...')
          pages.push(total)
        } else if (current >= total - 3) {
          pages.push(1)
          pages.push('...')
          for (let i = total - 4; i <= total; i++) pages.push(i)
        } else {
          pages.push(1)
          pages.push('...')
          for (let i = current - 1; i <= current + 1; i++) pages.push(i)
          pages.push('...')
          pages.push(total)
        }
      }
      
      return pages
    })
    
    const startItem = computed(() => (props.currentPage - 1) * props.perPage + 1)
    const endItem = computed(() => Math.min(props.currentPage * props.perPage, props.total))
    
    return { displayPages, startItem, endItem }
  }
}
</script>