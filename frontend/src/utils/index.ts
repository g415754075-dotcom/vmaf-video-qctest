import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// 合并 Tailwind 类名
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 格式化文件大小
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化时长
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 格式化比特率
export function formatBitrate(bps: number): string {
  if (bps === 0) return 'N/A'
  const mbps = bps / 1_000_000
  return `${mbps.toFixed(2)} Mbps`
}

// 获取质量等级
export function getQualityLevel(vmafScore: number): { level: string; color: string } {
  if (vmafScore > 90) return { level: '优秀', color: 'text-green-600' }
  if (vmafScore > 80) return { level: '良好', color: 'text-blue-600' }
  if (vmafScore > 70) return { level: '可接受', color: 'text-yellow-600' }
  return { level: '差', color: 'text-red-600' }
}

// 获取状态文字和颜色
export function getStatusDisplay(status: string): { text: string; color: string; bgColor: string } {
  switch (status) {
    case 'pending':
      return { text: '等待中', color: 'text-gray-600', bgColor: 'bg-gray-100' }
    case 'running':
      return { text: '处理中', color: 'text-blue-600', bgColor: 'bg-blue-100' }
    case 'completed':
      return { text: '已完成', color: 'text-green-600', bgColor: 'bg-green-100' }
    case 'failed':
      return { text: '失败', color: 'text-red-600', bgColor: 'bg-red-100' }
    case 'cancelled':
      return { text: '已取消', color: 'text-orange-600', bgColor: 'bg-orange-100' }
    default:
      return { text: status, color: 'text-gray-600', bgColor: 'bg-gray-100' }
  }
}

// 计算分片数量
export function calculateChunks(fileSize: number, chunkSize: number = 10 * 1024 * 1024): number {
  return Math.ceil(fileSize / chunkSize)
}

// 格式化日期
export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 生成颜色（用于图表）
export function generateColor(index: number): string {
  const colors = [
    '#3b82f6', // blue
    '#ef4444', // red
    '#22c55e', // green
    '#f59e0b', // amber
    '#8b5cf6', // violet
    '#ec4899', // pink
    '#14b8a6', // teal
    '#f97316', // orange
  ]
  return colors[index % colors.length]
}
