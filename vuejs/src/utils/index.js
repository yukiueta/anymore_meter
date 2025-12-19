import helper from './helper'

export default app => {
  app.use(helper)
}

export const formatDate = (dateString) => {
  if (dateString) {
    const date = new Date(dateString)
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' }
    return date.toLocaleDateString('ja-JP', options)
  } else {
    return ""
  }
}

export const formatDateShort = (dateString) => {
  if (dateString) {
    const date = new Date(dateString)
    const options = { month: 'long', day: 'numeric' }
    return date.toLocaleDateString('ja-JP', options)
  } else {
    return ""
  }
}

export const formatDateTime = (dateString) => {
  if (dateString) {
    const date = new Date(dateString)
    if (isNaN(date.getTime()) || typeof dateString !== 'string' || !dateString.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
      return dateString
    }
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()
    const hours = date.getHours()
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}年${month}月${day}日${hours}:${minutes}`
  } else {
    return dateString
  }
}

export const truncateText = (text, length) => {
  if (text && text.length > length) {
    return text.slice(0, length) + '...'
  }
  return text
}

export const formatCurrency = (value) => {
  if (value) {
    return value.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
  } else {
    return value
  }
}