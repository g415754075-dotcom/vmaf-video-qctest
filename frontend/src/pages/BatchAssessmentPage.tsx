import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  FileText,
  RefreshCw,
  ExternalLink,
} from 'lucide-react'
import { getBatchStatus, createBatchReport } from '@/services/api'
import ScatterChart from '@/components/ScatterChart'
import ConclusionTable from '@/components/ConclusionTable'
import type { BatchAssessment, AssessmentDetail } from '@/types'

// 状态标签组件
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-yellow-100 text-yellow-700',
  }

  const labels: Record<string, string> = {
    pending: '等待中',
    running: '进行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {labels[status] || status}
    </span>
  )
}

// 单个任务卡片
function TaskCard({ assessment }: { assessment: AssessmentDetail }) {
  const navigate = useNavigate()

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => navigate(`/assessments/${assessment.id}`)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">
            {assessment.distorted_video.original_filename}
          </p>
          <p className="text-sm text-gray-500">
            {assessment.distorted_video.width}x{assessment.distorted_video.height} |{' '}
            {assessment.distorted_video.codec}
          </p>
        </div>
        <StatusBadge status={assessment.status} />
      </div>

      {/* 进度条 */}
      {assessment.status === 'running' && (
        <div className="mb-3">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>进度</span>
            <span>{assessment.progress.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all"
              style={{ width: `${assessment.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 评估结果 */}
      {assessment.status === 'completed' && assessment.vmaf_score && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-gray-500">VMAF</p>
            <p className="font-bold text-primary-600">{assessment.vmaf_score.toFixed(2)}</p>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-gray-500">SSIM</p>
            <p className="font-bold text-primary-600">
              {assessment.ssim_score ? assessment.ssim_score.toFixed(4) : '-'}
            </p>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <p className="text-xs text-gray-500">PSNR</p>
            <p className="font-bold text-primary-600">
              {assessment.psnr_score ? assessment.psnr_score.toFixed(2) : '-'}
            </p>
          </div>
        </div>
      )}

      {/* 失败信息 */}
      {assessment.status === 'failed' && assessment.error_message && (
        <p className="text-sm text-red-600 truncate">{assessment.error_message}</p>
      )}

      <div className="mt-3 flex justify-end">
        <span className="text-sm text-primary-600 flex items-center">
          查看详情 <ExternalLink className="h-4 w-4 ml-1" />
        </span>
      </div>
    </div>
  )
}

export default function BatchAssessmentPage() {
  const { batchId } = useParams<{ batchId: string }>()
  const navigate = useNavigate()
  const [batchData, setBatchData] = useState<BatchAssessment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  // 加载批量评估状态
  const loadBatchStatus = async () => {
    if (!batchId) return

    try {
      const data = await getBatchStatus(batchId)
      setBatchData(data)
      setError(null)
    } catch (err) {
      console.error('加载批量评估状态失败:', err)
      setError('加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始加载和轮询
  useEffect(() => {
    loadBatchStatus()

    // 如果有任务在进行中，则轮询
    const interval = setInterval(() => {
      if (batchData && batchData.progress < 100) {
        loadBatchStatus()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [batchId, batchData?.progress])

  // 生成对比报告
  const handleGenerateReport = async () => {
    if (!batchData || !batchId) return

    const completedCount = batchData.assessments.filter((a) => a.status === 'completed').length

    if (completedCount === 0) {
      alert('没有已完成的评估任务')
      return
    }

    setGenerating(true)
    try {
      const result = await createBatchReport(batchId)
      alert(result.message)
      navigate('/reports')
    } catch (err) {
      console.error('生成报告失败:', err)
      alert('生成报告失败')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error || !batchData) {
    return (
      <div className="text-center py-12">
        <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-600">{error || '批量评估不存在'}</p>
        <button
          onClick={() => navigate('/upload')}
          className="mt-4 text-primary-600 hover:text-primary-700"
        >
          返回上传页面
        </button>
      </div>
    )
  }

  const isComplete = batchData.progress >= 100
  const hasCompleted = batchData.completed_count > 0

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => navigate(-1)}
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">批量评估</h1>
            <p className="text-gray-600 mt-1">
              参考视频: {batchData.reference_video.original_filename}
            </p>
          </div>
        </div>
        <button
          onClick={loadBatchStatus}
          className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900"
        >
          <RefreshCw className="h-5 w-5 mr-2" />
          刷新
        </button>
      </div>

      {/* 整体进度 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">评估进度</h2>
          <div className="flex items-center gap-4">
            {isComplete ? (
              <span className="flex items-center text-green-600">
                <CheckCircle className="h-5 w-5 mr-1" />
                全部完成
              </span>
            ) : (
              <span className="flex items-center text-blue-600">
                <Loader2 className="h-5 w-5 mr-1 animate-spin" />
                评估中...
              </span>
            )}
          </div>
        </div>

        {/* 进度条 */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>
              {batchData.completed_count}/{batchData.total_count} 已完成
              {batchData.failed_count > 0 && (
                <span className="text-red-600 ml-2">({batchData.failed_count} 失败)</span>
              )}
            </span>
            <span>{batchData.progress.toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 rounded-full transition-all"
              style={{ width: `${batchData.progress}%` }}
            />
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <Clock className="h-6 w-6 text-gray-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-700">{batchData.total_count}</p>
            <p className="text-sm text-gray-500">总任务数</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <CheckCircle className="h-6 w-6 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-green-600">{batchData.completed_count}</p>
            <p className="text-sm text-gray-500">已完成</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <Loader2 className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-blue-600">
              {batchData.assessments.filter((a) => a.status === 'running').length}
            </p>
            <p className="text-sm text-gray-500">进行中</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4 text-center">
            <XCircle className="h-6 w-6 text-red-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-red-600">{batchData.failed_count}</p>
            <p className="text-sm text-gray-500">失败</p>
          </div>
        </div>
      </div>

      {/* 散点图（完成后显示） */}
      {hasCompleted && <ScatterChart assessments={batchData.assessments} />}

      {/* 结论表格（完成后显示） */}
      {hasCompleted && <ConclusionTable assessments={batchData.assessments} />}

      {/* 任务列表 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">评估任务</h2>
          {hasCompleted && (
            <button
              onClick={handleGenerateReport}
              disabled={generating}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300"
            >
              <FileText className="h-5 w-5 mr-2" />
              {generating ? '生成中...' : '生成对比报告'}
            </button>
          )}
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {batchData.assessments.map((assessment) => (
            <TaskCard key={assessment.id} assessment={assessment} />
          ))}
        </div>
      </div>
    </div>
  )
}
