import { Link } from 'react-router-dom'
import { Play, XCircle, Eye, BarChart2 } from 'lucide-react'
import { cn, formatDate, getStatusDisplay, getQualityLevel } from '@/utils'
import type { AssessmentDetail } from '@/types'

interface AssessmentCardProps {
  assessment: AssessmentDetail
  onStart?: () => void
  onCancel?: () => void
}

export default function AssessmentCard({ assessment, onStart, onCancel }: AssessmentCardProps) {
  const status = getStatusDisplay(assessment.status)
  const quality = assessment.vmaf_score ? getQualityLevel(assessment.vmaf_score) : null

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="p-4">
        {/* 标题和状态 */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-medium text-gray-900">评估任务 #{assessment.id}</h3>
            <p className="text-sm text-gray-500">{formatDate(assessment.created_at)}</p>
          </div>
          <span className={cn('px-2 py-1 text-xs font-medium rounded', status.bgColor, status.color)}>
            {status.text}
          </span>
        </div>

        {/* 视频信息 */}
        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <p className="text-gray-500 mb-1">参考视频</p>
            <p className="font-medium text-gray-900 truncate" title={assessment.reference_video.original_filename}>
              {assessment.reference_video.original_filename}
            </p>
          </div>
          <div>
            <p className="text-gray-500 mb-1">待测视频</p>
            <p className="font-medium text-gray-900 truncate" title={assessment.distorted_video.original_filename}>
              {assessment.distorted_video.original_filename}
            </p>
          </div>
        </div>

        {/* 进度条（运行中） */}
        {assessment.status === 'running' && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>处理进度</span>
              <span>
                {assessment.current_frame} / {assessment.total_frames} 帧 ({assessment.progress.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${assessment.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* 评估结果（已完成） */}
        {assessment.status === 'completed' && (
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{assessment.vmaf_score?.toFixed(1) || 'N/A'}</p>
              <p className="text-xs text-gray-500">VMAF</p>
              {quality && <p className={cn('text-xs font-medium', quality.color)}>{quality.level}</p>}
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{assessment.ssim_score?.toFixed(4) || 'N/A'}</p>
              <p className="text-xs text-gray-500">SSIM</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">{assessment.psnr_score?.toFixed(2) || 'N/A'}</p>
              <p className="text-xs text-gray-500">PSNR (dB)</p>
            </div>
          </div>
        )}

        {/* 错误信息 */}
        {assessment.status === 'failed' && assessment.error_message && (
          <div className="mb-4 p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-600">{assessment.error_message}</p>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            {assessment.status === 'pending' && onStart && (
              <button
                onClick={onStart}
                className="flex items-center px-3 py-1.5 text-sm font-medium text-white bg-primary-500 rounded hover:bg-primary-600"
              >
                <Play className="h-4 w-4 mr-1" />
                开始
              </button>
            )}
            {assessment.status === 'running' && onCancel && (
              <button
                onClick={onCancel}
                className="flex items-center px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 rounded hover:bg-red-100"
              >
                <XCircle className="h-4 w-4 mr-1" />
                取消
              </button>
            )}
          </div>

          {assessment.status === 'completed' && (
            <Link
              to={`/assessments/${assessment.id}`}
              className="flex items-center px-3 py-1.5 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              <Eye className="h-4 w-4 mr-1" />
              查看详情
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
