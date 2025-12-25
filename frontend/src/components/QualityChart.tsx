import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { cn, generateColor } from '@/utils'
import type { FrameQuality } from '@/types'

interface QualityChartProps {
  data: FrameQuality[]
  metric?: 'vmaf' | 'ssim' | 'psnr'
  comparisonData?: { name: string; data: FrameQuality[] }[]
  height?: number
}

export default function QualityChart({
  data,
  metric = 'vmaf',
  comparisonData,
  height = 400,
}: QualityChartProps) {
  const [activeMetric, setActiveMetric] = useState(metric)

  // 准备图表数据
  const chartData = data.map((frame, index) => ({
    frame: frame.frame_num,
    vmaf: frame.vmaf,
    ssim: frame.ssim,
    psnr: frame.psnr,
    // 添加对比数据
    ...comparisonData?.reduce(
      (acc, item) => ({
        ...acc,
        [`${item.name}_${activeMetric}`]: item.data[index]?.[activeMetric],
      }),
      {}
    ),
  }))

  // Y 轴范围
  const getYAxisDomain = () => {
    switch (activeMetric) {
      case 'vmaf':
        return [0, 100]
      case 'ssim':
        return [0, 1]
      case 'psnr':
        return [0, 60]
      default:
        return [0, 100]
    }
  }

  // 参考线值
  const getReferenceLines = () => {
    switch (activeMetric) {
      case 'vmaf':
        return [
          { value: 90, label: '优秀', color: '#22c55e' },
          { value: 80, label: '良好', color: '#3b82f6' },
          { value: 70, label: '可接受', color: '#f59e0b' },
        ]
      case 'ssim':
        return [
          { value: 0.98, label: '优秀', color: '#22c55e' },
          { value: 0.95, label: '良好', color: '#3b82f6' },
        ]
      case 'psnr':
        return [
          { value: 40, label: '优秀', color: '#22c55e' },
          { value: 35, label: '良好', color: '#3b82f6' },
        ]
      default:
        return []
    }
  }

  const metrics = [
    { key: 'vmaf', label: 'VMAF', unit: '' },
    { key: 'ssim', label: 'SSIM', unit: '' },
    { key: 'psnr', label: 'PSNR', unit: 'dB' },
  ] as const

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* 指标切换 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-gray-900">质量曲线</h3>
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {metrics.map((m) => (
            <button
              key={m.key}
              onClick={() => setActiveMetric(m.key)}
              className={cn(
                'px-3 py-1 text-sm font-medium rounded transition-colors',
                activeMetric === m.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* 图表 */}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="frame"
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(value) => `${value}`}
          />
          <YAxis
            domain={getYAxisDomain()}
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(value) =>
              activeMetric === 'ssim' ? value.toFixed(2) : value.toFixed(0)
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) =>
              activeMetric === 'ssim' ? value.toFixed(4) : value.toFixed(2)
            }
            labelFormatter={(label) => `帧 ${label}`}
          />
          <Legend />

          {/* 参考线 */}
          {getReferenceLines().map((ref) => (
            <ReferenceLine
              key={ref.value}
              y={ref.value}
              stroke={ref.color}
              strokeDasharray="5 5"
              label={{
                value: ref.label,
                position: 'right',
                fill: ref.color,
                fontSize: 12,
              }}
            />
          ))}

          {/* 主曲线 */}
          <Line
            type="monotone"
            dataKey={activeMetric}
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="当前视频"
          />

          {/* 对比曲线 */}
          {comparisonData?.map((item, index) => (
            <Line
              key={item.name}
              type="monotone"
              dataKey={`${item.name}_${activeMetric}`}
              stroke={generateColor(index + 1)}
              strokeWidth={2}
              dot={false}
              name={item.name}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
