import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  Label,
  LabelList,
} from 'recharts'
import type { AssessmentDetail } from '@/types'

interface ScatterChartProps {
  assessments: AssessmentDetail[]
}

// 根据 VMAF 分数获取颜色
function getColor(vmaf: number): string {
  if (vmaf > 93) return '#22c55e' // green
  if (vmaf > 85) return '#84cc16' // lime
  if (vmaf > 70) return '#eab308' // yellow
  if (vmaf > 50) return '#f97316' // orange
  return '#ef4444' // red
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(2)} GB`
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(2)} MB`
  return `${(bytes / 1_000).toFixed(2)} KB`
}

// 自定义 Tooltip - 通用版本
function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
        <p className="font-medium text-gray-900 mb-2 truncate" title={data.name}>
          {data.name.length > 25 ? data.name.substring(0, 25) + '...' : data.name}
        </p>
        <div className="space-y-1 text-sm">
          <p className="text-gray-600">
            VMAF: <span className="font-medium text-primary-600">{data.vmaf.toFixed(2)}</span>
          </p>
          <p className="text-gray-600">
            码率: <span className="font-medium">{data.bitrate.toFixed(2)} Mbps</span>
          </p>
          <p className="text-gray-600">
            文件大小: <span className="font-medium">{formatFileSize(data.fileSize)}</span>
          </p>
          <p className="text-gray-600">
            编码: <span className="font-medium">{data.codec}</span>
          </p>
        </div>
      </div>
    )
  }
  return null
}

// 单个散点图组件
function SingleScatterChart({
  data,
  xKey,
  yKey,
  xLabel,
  yLabel,
  xUnit,
  yUnit,
  xDomain,
  yDomain,
  title,
  description,
  referenceLines,
}: {
  data: any[]
  xKey: string
  yKey: string
  xLabel: string
  yLabel: string
  xUnit?: string
  yUnit?: string
  xDomain?: [number, number] | ['auto', 'auto']
  yDomain?: [number, number] | ['auto', 'auto']
  title: string
  description: string
  referenceLines?: { y?: number; x?: number; label: string; color: string }[]
}) {
  return (
    <div className="flex-1 min-w-0">
      <h4 className="text-sm font-semibold text-gray-800 mb-1 text-center">{title}</h4>
      <p className="text-xs text-gray-500 mb-2 text-center">{description}</p>
      <ResponsiveContainer width="100%" height={280}>
        <RechartsScatterChart margin={{ top: 10, right: 10, bottom: 30, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey={xKey}
            domain={xDomain || ['auto', 'auto']}
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => xUnit === 'MB' ? v.toFixed(1) : v.toFixed(1)}
          >
            <Label value={`${xLabel}${xUnit ? ` (${xUnit})` : ''}`} position="bottom" offset={10} style={{ fontSize: 11, fill: '#6b7280' }} />
          </XAxis>
          <YAxis
            type="number"
            dataKey={yKey}
            domain={yDomain || ['auto', 'auto']}
            tick={{ fontSize: 10 }}
            tickFormatter={(v) => yUnit === 'MB' ? v.toFixed(1) : v.toFixed(1)}
          >
            <Label value={`${yLabel}${yUnit ? ` (${yUnit})` : ''}`} angle={-90} position="insideLeft" offset={5} style={{ fontSize: 11, fill: '#6b7280', textAnchor: 'middle' }} />
          </YAxis>

          {/* 参考线 */}
          {referenceLines?.map((ref, idx) => (
            ref.y !== undefined ? (
              <ReferenceLine
                key={idx}
                y={ref.y}
                stroke={ref.color}
                strokeDasharray="4 4"
                strokeWidth={1}
              />
            ) : ref.x !== undefined ? (
              <ReferenceLine
                key={idx}
                x={ref.x}
                stroke={ref.color}
                strokeDasharray="4 4"
                strokeWidth={1}
              />
            ) : null
          ))}

          <Tooltip content={<CustomTooltip />} />

          <Scatter data={data}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.vmaf)} r={8} />
            ))}
            <LabelList
              dataKey="shortName"
              position="top"
              offset={10}
              style={{ fontSize: 9, fill: '#374151', fontWeight: 500 }}
            />
          </Scatter>
        </RechartsScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

// 生成简短的视频名称（去除扩展名，截取前12个字符）
function getShortName(filename: string): string {
  const nameWithoutExt = filename.replace(/\.[^/.]+$/, '')
  return nameWithoutExt.length > 12 ? nameWithoutExt.substring(0, 12) + '…' : nameWithoutExt
}

export default function ScatterChart({ assessments }: ScatterChartProps) {
  // 转换数据格式
  const data = assessments
    .filter((a) => a.status === 'completed' && a.vmaf_score)
    .map((a) => ({
      name: a.distorted_video.original_filename,
      shortName: getShortName(a.distorted_video.original_filename),
      vmaf: a.vmaf_score || 0,
      bitrate: (a.distorted_video.bitrate || 0) / 1_000_000, // Mbps
      fileSize: a.distorted_video.file_size || 0, // bytes
      fileSizeMB: (a.distorted_video.file_size || 0) / 1_000_000, // MB
      codec: a.distorted_video.codec || 'N/A',
    }))

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">暂无数据</p>
      </div>
    )
  }

  // 计算各轴范围
  const maxBitrate = Math.max(...data.map((d) => d.bitrate))
  const maxFileSizeMB = Math.max(...data.map((d) => d.fileSizeMB))
  const minVmaf = Math.min(...data.map((d) => d.vmaf))

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">质量对比分析图</h3>
      <p className="text-sm text-gray-500 mb-4">
        三张散点图从不同维度展示各视频的质量、文件大小和 VMAF 分数之间的关系，帮助您选择最佳编码方案。
      </p>

      {/* 三张并排的散点图 */}
      <div className="flex gap-4">
        {/* 左图：码率 vs 文件大小 (Quality vs Size) */}
        <SingleScatterChart
          data={data}
          xKey="bitrate"
          yKey="fileSizeMB"
          xLabel="码率"
          yLabel="文件大小"
          xUnit="Mbps"
          yUnit="MB"
          xDomain={[0, Math.ceil(maxBitrate * 1.1)]}
          yDomain={[0, Math.ceil(maxFileSizeMB * 1.1)]}
          title="码率 vs 文件大小"
          description="查看不同码率下文件大小的变化"
        />

        {/* 中图：码率 vs VMAF (Quality vs VMAF) */}
        <SingleScatterChart
          data={data}
          xKey="bitrate"
          yKey="vmaf"
          xLabel="码率"
          yLabel="VMAF"
          xUnit="Mbps"
          xDomain={[0, Math.ceil(maxBitrate * 1.1)]}
          yDomain={[Math.max(0, Math.floor(minVmaf - 5)), 100]}
          title="码率 vs VMAF"
          description="查看码率与画质之间的对应关系"
          referenceLines={[
            { y: 93, label: '优秀', color: '#22c55e' },
            { y: 70, label: '可接受', color: '#eab308' },
          ]}
        />

        {/* 右图：VMAF vs 文件大小 (VMAF vs Size) */}
        <SingleScatterChart
          data={data}
          xKey="vmaf"
          yKey="fileSizeMB"
          xLabel="VMAF"
          yLabel="文件大小"
          yUnit="MB"
          xDomain={[Math.max(0, Math.floor(minVmaf - 5)), 100]}
          yDomain={[0, Math.ceil(maxFileSizeMB * 1.1)]}
          title="VMAF vs 文件大小"
          description="查看画质提升带来的体积成本"
          referenceLines={[
            { x: 93, label: '优秀', color: '#22c55e' },
            { x: 70, label: '可接受', color: '#eab308' },
          ]}
        />
      </div>

      {/* 图例 */}
      <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4 text-xs">
          <span className="text-gray-500 font-medium">VMAF 质量等级:</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
            <span className="text-gray-600">优秀 (&gt;93)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-[#84cc16]" />
            <span className="text-gray-600">良好 (85-93)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-[#eab308]" />
            <span className="text-gray-600">可接受 (70-85)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-[#f97316]" />
            <span className="text-gray-600">较差 (50-70)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
            <span className="text-gray-600">很差 (&lt;50)</span>
          </div>
        </div>
      </div>

      {/* 解读说明 */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600 font-medium mb-2">图表解读:</p>
        <ul className="text-xs text-gray-500 space-y-1">
          <li>• <strong>左图 (码率 vs 文件大小):</strong> 斜率越陡表示编码效率越低，相同码率下文件更大</li>
          <li>• <strong>中图 (码率 vs VMAF):</strong> 曲线趋于平缓的位置是最佳码率点，再增加码率收益不大</li>
          <li>• <strong>右图 (VMAF vs 文件大小):</strong> 越靠右下角的点性价比越高（高质量、小体积）</li>
        </ul>
      </div>
    </div>
  )
}
