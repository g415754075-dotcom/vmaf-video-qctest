import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, FileText, AlertTriangle } from 'lucide-react'
import QualityChart from '@/components/QualityChart'
import { getAssessment, getFrameData, getStatistics, getProblemFrames, createReport } from '@/services/api'
import { formatDate, getQualityLevel, getStatusDisplay, cn } from '@/utils'
import type { AssessmentDetail, FrameQuality } from '@/types'

export default function AssessmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null)
  const [frameData, setFrameData] = useState<FrameQuality[]>([])
  const [statistics, setStatistics] = useState<any>(null)
  const [problemFrames, setProblemFrames] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    if (id) {
      loadData(parseInt(id))
    }
  }, [id])

  const loadData = async (assessmentId: number) => {
    setLoading(true)
    try {
      const [assessmentData, framesResult, stats, problems] = await Promise.all([
        getAssessment(assessmentId),
        getFrameData(assessmentId, { limit: 5000 }).catch(() => ({ frames: [] })),
        getStatistics(assessmentId).catch(() => null),
        getProblemFrames(assessmentId, 70, 10).catch(() => ({ frames: [] })),
      ])

      setAssessment(assessmentData)
      setFrameData(framesResult.frames)
      setStatistics(stats)
      setProblemFrames(problems.frames || [])
    } catch (error) {
      console.error('加载评估详情失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    if (!assessment) return

    setGenerating(true)
    try {
      await createReport(
        `评估报告_${assessment.distorted_video.original_filename}`,
        [assessment.id]
      )
      alert('报告生成成功！')
      // 可以跳转到报告页面
    } catch (error) {
      console.error('生成报告失败:', error)
      alert('生成报告失败')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!assessment) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">评估任务不存在</p>
        <Link to="/assessments" className="text-primary-600 hover:text-primary-700 mt-2 inline-block">
          返回列表
        </Link>
      </div>
    )
  }

  const status = getStatusDisplay(assessment.status)
  const quality = assessment.vmaf_score ? getQualityLevel(assessment.vmaf_score) : null

  return (
    <div className="space-y-6">
      {/* 返回链接 */}
      <Link
        to="/assessments"
        className="inline-flex items-center text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        返回任务列表
      </Link>

      {/* 标题和操作 */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评估任务 #{assessment.id}</h1>
          <p className="text-gray-600 mt-1">{formatDate(assessment.created_at)}</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className={cn('px-3 py-1 text-sm font-medium rounded-full', status.bgColor, status.color)}>
            {status.text}
          </span>
          {assessment.status === 'completed' && (
            <button
              onClick={handleGenerateReport}
              disabled={generating}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-300"
            >
              <FileText className="h-4 w-4 mr-2" />
              {generating ? '生成中...' : '生成报告'}
            </button>
          )}
        </div>
      </div>

      {/* 视频信息 */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-medium text-gray-500 mb-2">参考视频</h3>
          <p className="font-semibold text-gray-900 truncate">{assessment.reference_video.original_filename}</p>
          <p className="text-sm text-gray-500 mt-1">
            {assessment.reference_video.width}x{assessment.reference_video.height} |{' '}
            {assessment.reference_video.codec?.toUpperCase()}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="font-medium text-gray-500 mb-2">待测视频</h3>
          <p className="font-semibold text-gray-900 truncate">{assessment.distorted_video.original_filename}</p>
          <p className="text-sm text-gray-500 mt-1">
            {assessment.distorted_video.width}x{assessment.distorted_video.height} |{' '}
            {assessment.distorted_video.codec?.toUpperCase()}
          </p>
        </div>
      </div>

      {/* 评估结果 */}
      {assessment.status === 'completed' && (
        <>
          {/* 分数卡片 */}
          <div className="grid md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
              <p className="text-4xl font-bold text-gray-900">{assessment.vmaf_score?.toFixed(1) || 'N/A'}</p>
              <p className="text-gray-500 mt-1">VMAF</p>
              {quality && <p className={cn('text-sm font-medium mt-1', quality.color)}>{quality.level}</p>}
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
              <p className="text-4xl font-bold text-gray-900">{assessment.ssim_score?.toFixed(4) || 'N/A'}</p>
              <p className="text-gray-500 mt-1">SSIM</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
              <p className="text-4xl font-bold text-gray-900">{assessment.psnr_score?.toFixed(2) || 'N/A'}</p>
              <p className="text-gray-500 mt-1">PSNR (dB)</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
              <p className="text-4xl font-bold text-gray-900">
                {assessment.vmaf_min?.toFixed(1)} - {assessment.vmaf_max?.toFixed(1)}
              </p>
              <p className="text-gray-500 mt-1">VMAF 范围</p>
            </div>
          </div>

          {/* 质量曲线 */}
          {frameData.length > 0 && <QualityChart data={frameData} height={400} />}

          {/* 统计信息 */}
          {statistics && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">统计分析</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="py-2 px-4 text-left font-medium text-gray-500">指标</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">平均值</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">最小值</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">最大值</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">中位数</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">标准差</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">P5</th>
                      <th className="py-2 px-4 text-right font-medium text-gray-500">P95</th>
                    </tr>
                  </thead>
                  <tbody>
                    {['vmaf', 'ssim', 'psnr'].map((metric) => {
                      const stats = statistics[metric]
                      if (!stats) return null
                      return (
                        <tr key={metric} className="border-b border-gray-100">
                          <td className="py-2 px-4 font-medium text-gray-900">{metric.toUpperCase()}</td>
                          <td className="py-2 px-4 text-right">{stats.mean?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.min?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.max?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.median?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.std?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.p5?.toFixed(2)}</td>
                          <td className="py-2 px-4 text-right">{stats.p95?.toFixed(2)}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 问题帧 */}
          {problemFrames.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center mb-4">
                <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
                <h3 className="font-semibold text-gray-900">问题帧（VMAF &lt; 70）</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {problemFrames.map((frame) => (
                  <div key={frame.frame_num} className="text-center p-3 bg-red-50 rounded-lg">
                    <p className="text-lg font-bold text-red-600">{frame.vmaf?.toFixed(1)}</p>
                    <p className="text-sm text-gray-500">帧 {frame.frame_num}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* 运行中状态 */}
      {assessment.status === 'running' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>处理进度</span>
            <span>
              {assessment.current_frame} / {assessment.total_frames} 帧 ({assessment.progress.toFixed(1)}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-primary-500 h-3 rounded-full transition-all duration-300"
              style={{ width: `${assessment.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 失败状态 */}
      {assessment.status === 'failed' && assessment.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="font-semibold text-red-800 mb-2">评估失败</h3>
          <p className="text-red-600">{assessment.error_message}</p>
        </div>
      )}
    </div>
  )
}
