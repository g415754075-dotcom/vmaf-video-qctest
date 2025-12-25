import { Link } from 'react-router-dom'
import { Star, Trophy, CheckCircle, AlertTriangle, XCircle, Ban } from 'lucide-react'
import type { AssessmentDetail } from '@/types'

interface ConclusionTableProps {
  assessments: AssessmentDetail[]
}

// 根据 VMAF 分数获取质量评级
function getQualityRating(vmaf: number) {
  if (vmaf > 93) {
    return {
      stars: 5,
      level: '优秀',
      description: '画质非常清晰，几乎无损',
      recommendation: '强烈推荐',
      RecommendIcon: Trophy,
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      borderColor: 'border-green-200',
    }
  } else if (vmaf > 85) {
    return {
      stars: 4,
      level: '良好',
      description: '画质清晰，轻微损失',
      recommendation: '推荐',
      RecommendIcon: CheckCircle,
      bgColor: 'bg-lime-50',
      textColor: 'text-lime-700',
      borderColor: 'border-lime-200',
    }
  } else if (vmaf > 70) {
    return {
      stars: 3,
      level: '可接受',
      description: '画质一般，有明显损失',
      recommendation: '可用',
      RecommendIcon: AlertTriangle,
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-700',
      borderColor: 'border-yellow-200',
    }
  } else if (vmaf > 50) {
    return {
      stars: 2,
      level: '较差',
      description: '画质模糊，损失较大',
      recommendation: '不推荐',
      RecommendIcon: XCircle,
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-700',
      borderColor: 'border-orange-200',
    }
  } else {
    return {
      stars: 1,
      level: '很差',
      description: '画质很差，严重失真',
      recommendation: '避免使用',
      RecommendIcon: Ban,
      bgColor: 'bg-red-50',
      textColor: 'text-red-700',
      borderColor: 'border-red-200',
    }
  }
}

// 计算码率效率
function getEfficiency(vmaf: number, bitrateMbps: number) {
  if (bitrateMbps <= 0) return { level: '未知', description: '无法计算' }

  const efficiency = vmaf / bitrateMbps

  if (efficiency > 30) return { level: '非常高', description: '极高性价比' }
  if (efficiency > 20) return { level: '高', description: '高性价比' }
  if (efficiency > 12) return { level: '中等', description: '性价比一般' }
  if (efficiency > 6) return { level: '低', description: '性价比较低' }
  return { level: '很低', description: '性价比很低' }
}

// 星级组件
function StarRating({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${i <= count ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
        />
      ))}
    </div>
  )
}

export default function ConclusionTable({ assessments }: ConclusionTableProps) {
  // 过滤并排序已完成的评估
  const completedAssessments = assessments
    .filter((a) => a.status === 'completed' && a.vmaf_score)
    .sort((a, b) => (b.vmaf_score || 0) - (a.vmaf_score || 0))

  if (completedAssessments.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-500">暂无已完成的评估结果</p>
      </div>
    )
  }

  // 找出最佳质量和最高效率
  const bestQuality = completedAssessments[0]
  const bestEfficiency = completedAssessments.reduce((best, current) => {
    const currentBitrate = (current.distorted_video.bitrate || 0) / 1_000_000
    const bestBitrate = (best.distorted_video.bitrate || 0) / 1_000_000
    const currentEff = currentBitrate > 0 ? (current.vmaf_score || 0) / currentBitrate : 0
    const bestEff = bestBitrate > 0 ? (best.vmaf_score || 0) / bestBitrate : 0
    return currentEff > bestEff ? current : best
  }, completedAssessments[0])

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">质量评估结论</h3>
        <p className="text-sm text-gray-500 mt-1">
          以下表格帮助您快速了解各视频的质量情况（按质量排序）
        </p>
      </div>

      {/* 推荐摘要 */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-green-200">
            <Trophy className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-500">最佳质量</p>
              <p className="font-medium text-gray-900 truncate">
                {bestQuality.distorted_video.original_filename}
              </p>
              <p className="text-sm text-green-600">
                VMAF: {bestQuality.vmaf_score?.toFixed(2)}
              </p>
            </div>
          </div>
          {bestEfficiency.id !== bestQuality.id && (
            <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-blue-200">
              <CheckCircle className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">最高性价比</p>
                <p className="font-medium text-gray-900 truncate">
                  {bestEfficiency.distorted_video.original_filename}
                </p>
                <p className="text-sm text-blue-600">
                  VMAF: {bestEfficiency.vmaf_score?.toFixed(2)} |{' '}
                  {((bestEfficiency.distorted_video.bitrate || 0) / 1_000_000).toFixed(2)} Mbps
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">排名</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">视频名称</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">质量评级</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">质量描述</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">推荐程度</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">码率效率</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {completedAssessments.map((assessment, index) => {
              const vmaf = assessment.vmaf_score || 0
              const bitrateMbps = (assessment.distorted_video.bitrate || 0) / 1_000_000
              const rating = getQualityRating(vmaf)
              const efficiency = getEfficiency(vmaf, bitrateMbps)
              const RecommendIcon = rating.RecommendIcon

              return (
                <tr
                  key={assessment.id}
                  className={`${rating.bgColor} hover:opacity-80 transition-opacity`}
                >
                  <td className="px-4 py-4">
                    <span
                      className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${
                        index === 0
                          ? 'bg-yellow-400 text-white'
                          : index === 1
                          ? 'bg-gray-300 text-gray-700'
                          : index === 2
                          ? 'bg-amber-600 text-white'
                          : 'bg-gray-100 text-gray-600'
                      } font-bold text-sm`}
                    >
                      {index + 1}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <Link
                      to={`/assessments/${assessment.id}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {assessment.distorted_video.original_filename}
                    </Link>
                    <p className="text-xs text-gray-500 mt-1">
                      {assessment.distorted_video.width}x{assessment.distorted_video.height} |{' '}
                      {bitrateMbps.toFixed(2)} Mbps
                    </p>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <div className="flex flex-col items-center gap-1">
                      <StarRating count={rating.stars} />
                      <span className={`text-sm font-medium ${rating.textColor}`}>
                        {rating.level}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <span className="text-sm text-gray-600">{rating.description}</span>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <RecommendIcon className={`h-5 w-5 ${rating.textColor}`} />
                      <span className={`text-sm font-medium ${rating.textColor}`}>
                        {rating.recommendation}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-center">
                    <span className="text-sm text-gray-600">{efficiency.level}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* 图例说明 */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          <strong>质量评级标准：</strong>
          优秀 (VMAF &gt; 93) | 良好 (85-93) | 可接受 (70-85) | 较差 (50-70) | 很差 (&lt; 50)
        </p>
        <p className="text-xs text-gray-500 mt-1">
          <strong>码率效率：</strong>
          VMAF 分数 / 码率(Mbps)，效率越高表示用更少的码率获得更好的质量
        </p>
      </div>
    </div>
  )
}
