import { describe, it, expect } from 'vitest'
import {
  formatFileSize,
  formatDuration,
  formatBitrate,
  getQualityLevel,
  getStatusDisplay,
  calculateChunks,
  formatDate,
  generateColor,
} from './index'

describe('formatFileSize', () => {
  it('应该正确格式化 0 字节', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })

  it('应该正确格式化字节', () => {
    expect(formatFileSize(500)).toBe('500 B')
  })

  it('应该正确格式化 KB', () => {
    expect(formatFileSize(1024)).toBe('1 KB')
    expect(formatFileSize(1536)).toBe('1.5 KB')
  })

  it('应该正确格式化 MB', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1 MB')
    expect(formatFileSize(1.5 * 1024 * 1024)).toBe('1.5 MB')
  })

  it('应该正确格式化 GB', () => {
    expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
    expect(formatFileSize(2.5 * 1024 * 1024 * 1024)).toBe('2.5 GB')
  })
})

describe('formatDuration', () => {
  it('应该正确格式化秒数', () => {
    expect(formatDuration(30)).toBe('0:30')
  })

  it('应该正确格式化分钟', () => {
    expect(formatDuration(90)).toBe('1:30')
    expect(formatDuration(600)).toBe('10:00')
  })

  it('应该正确格式化小时', () => {
    expect(formatDuration(3600)).toBe('1:00:00')
    expect(formatDuration(3661)).toBe('1:01:01')
    expect(formatDuration(7265)).toBe('2:01:05')
  })

  it('应该补零显示', () => {
    expect(formatDuration(61)).toBe('1:01')
    expect(formatDuration(3601)).toBe('1:00:01')
  })
})

describe('formatBitrate', () => {
  it('应该返回 N/A 当比特率为 0', () => {
    expect(formatBitrate(0)).toBe('N/A')
  })

  it('应该正确格式化 Mbps', () => {
    expect(formatBitrate(5000000)).toBe('5.00 Mbps')
    expect(formatBitrate(2500000)).toBe('2.50 Mbps')
    expect(formatBitrate(10000000)).toBe('10.00 Mbps')
  })
})

describe('getQualityLevel', () => {
  it('应该返回优秀当 VMAF > 90', () => {
    const result = getQualityLevel(95)
    expect(result.level).toBe('优秀')
    expect(result.color).toBe('text-green-600')
  })

  it('应该返回良好当 VMAF 在 80-90 之间', () => {
    const result = getQualityLevel(85)
    expect(result.level).toBe('良好')
    expect(result.color).toBe('text-blue-600')
  })

  it('应该返回可接受当 VMAF 在 70-80 之间', () => {
    const result = getQualityLevel(75)
    expect(result.level).toBe('可接受')
    expect(result.color).toBe('text-yellow-600')
  })

  it('应该返回差当 VMAF <= 70', () => {
    const result = getQualityLevel(65)
    expect(result.level).toBe('差')
    expect(result.color).toBe('text-red-600')
  })

  it('应该正确处理边界值', () => {
    expect(getQualityLevel(90).level).toBe('良好')
    expect(getQualityLevel(90.1).level).toBe('优秀')
    expect(getQualityLevel(80).level).toBe('可接受')
    expect(getQualityLevel(80.1).level).toBe('良好')
    expect(getQualityLevel(70).level).toBe('差')
    expect(getQualityLevel(70.1).level).toBe('可接受')
  })
})

describe('getStatusDisplay', () => {
  it('应该返回等待中状态', () => {
    const result = getStatusDisplay('pending')
    expect(result.text).toBe('等待中')
    expect(result.color).toBe('text-gray-600')
    expect(result.bgColor).toBe('bg-gray-100')
  })

  it('应该返回处理中状态', () => {
    const result = getStatusDisplay('running')
    expect(result.text).toBe('处理中')
    expect(result.color).toBe('text-blue-600')
    expect(result.bgColor).toBe('bg-blue-100')
  })

  it('应该返回已完成状态', () => {
    const result = getStatusDisplay('completed')
    expect(result.text).toBe('已完成')
    expect(result.color).toBe('text-green-600')
    expect(result.bgColor).toBe('bg-green-100')
  })

  it('应该返回失败状态', () => {
    const result = getStatusDisplay('failed')
    expect(result.text).toBe('失败')
    expect(result.color).toBe('text-red-600')
    expect(result.bgColor).toBe('bg-red-100')
  })

  it('应该返回已取消状态', () => {
    const result = getStatusDisplay('cancelled')
    expect(result.text).toBe('已取消')
    expect(result.color).toBe('text-orange-600')
    expect(result.bgColor).toBe('bg-orange-100')
  })

  it('应该返回原始状态当未知状态', () => {
    const result = getStatusDisplay('unknown')
    expect(result.text).toBe('unknown')
  })
})

describe('calculateChunks', () => {
  it('应该正确计算分片数量', () => {
    const chunkSize = 10 * 1024 * 1024 // 10MB
    expect(calculateChunks(0, chunkSize)).toBe(0)
    expect(calculateChunks(chunkSize, chunkSize)).toBe(1)
    expect(calculateChunks(chunkSize + 1, chunkSize)).toBe(2)
    expect(calculateChunks(chunkSize * 3, chunkSize)).toBe(3)
    expect(calculateChunks(chunkSize * 3.5, chunkSize)).toBe(4)
  })

  it('应该使用默认分片大小', () => {
    // 默认 10MB
    expect(calculateChunks(10 * 1024 * 1024)).toBe(1)
    expect(calculateChunks(25 * 1024 * 1024)).toBe(3)
  })
})

describe('formatDate', () => {
  it('应该正确格式化日期', () => {
    // 注意: 这个测试可能因时区不同而有差异
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(result).toMatch(/2024/)
    expect(result).toMatch(/01/)
    expect(result).toMatch(/15/)
  })
})

describe('generateColor', () => {
  it('应该按顺序返回颜色', () => {
    expect(generateColor(0)).toBe('#3b82f6') // blue
    expect(generateColor(1)).toBe('#ef4444') // red
    expect(generateColor(2)).toBe('#22c55e') // green
  })

  it('应该循环颜色', () => {
    // 有 8 种颜色
    expect(generateColor(0)).toBe(generateColor(8))
    expect(generateColor(1)).toBe(generateColor(9))
  })
})
