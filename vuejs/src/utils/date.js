/**
 * 日付フォーマットユーティリティ
 */

/**
 * 日付を「2023年12月01日」形式でフォーマット
 * @param {string|Date} date - 日付
 * @returns {string} フォーマットされた日付
 */
export const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}年${month}月${day}日`
}

/**
 * 日時を「2023年12月01日 14:30」形式でフォーマット
 * @param {string|Date} date - 日時
 * @returns {string} フォーマットされた日時
 */
export const formatDateTime = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${year}年${month}月${day}日 ${hour}:${min}`
}

/**
 * 日付を「2023-12-01」形式でフォーマット（ISO形式）
 * @param {string|Date} date - 日付
 * @returns {string} フォーマットされた日付
 */
export const formatDateISO = (date) => {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 日付を「2023年12月」形式でフォーマット
 * @param {string|Date} date - 日付
 * @returns {string} フォーマットされた年月
 */
export const formatYearMonth = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  return `${year}年${month}月`
}