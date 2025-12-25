import { useEffect, useState, useRef } from 'react'
import { RefreshCw, Plus, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import AssessmentCard from '@/components/AssessmentCard'
import { useStore } from '@/stores/useStore'
import { getAssessments, startAssessment, cancelAssessment, clearAllAssessments } from '@/services/api'

export default function AssessmentsPage() {
  const { assessments, setAssessments } = useStore()
  const [loading, setLoading] = useState(false)

  // 加载评估任务列表
  const loadAssessments = async () => {
    setLoading(true)
    try {
      const result = await getAssessments({ limit: 100 })
      setAssessments(result.assessments)
    } catch (error) {
      console.error('加载评估任务失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 使用 ref 来追踪是否有运行中的任务，避免闭包问题
  const hasRunningRef = useRef(false)

  useEffect(() => {
    hasRunningRef.current = assessments.some((a) => a.status === 'running')
  }, [assessments])

  useEffect(() => {
    loadAssessments()

    // 定时刷新运行中的任务（每 500ms 检查一次）
    const interval = setInterval(() => {
      if (hasRunningRef.current) {
        loadAssessments()
      }
    }, 500)

    return () => clearInterval(interval)
  }, [])

  // 启动任务
  const handleStart = async (id: number) => {
    try {
      await startAssessment(id)
      loadAssessments()
    } catch (error) {
      console.error('启动任务失败:', error)
      alert('启动任务失败')
    }
  }

  // 取消任务
  const handleCancel = async (id: number) => {
    if (!confirm('确定要取消这个任务吗？')) return

    try {
      await cancelAssessment(id)
      loadAssessments()
    } catch (error) {
      console.error('取消任务失败:', error)
      alert('取消任务失败')
    }
  }

  // 清空所有任务
  const handleClearAll = async () => {
    if (!confirm('确定要清空所有评估任务吗？运行中的任务将被跳过。此操作无法恢复！')) return

    setLoading(true)
    try {
      const result = await clearAllAssessments()
      let message = result.message
      if (result.running_count > 0) {
        message += `（${result.running_count} 个运行中的任务被跳过）`
      }
      alert(message)
      loadAssessments()
    } catch (error) {
      console.error('清空任务失败:', error)
      alert('清空任务失败')
    } finally {
      setLoading(false)
    }
  }

  // 按状态分组
  const runningAssessments = assessments.filter((a) => a.status === 'running')
  const pendingAssessments = assessments.filter((a) => a.status === 'pending')
  const completedAssessments = assessments.filter((a) => a.status === 'completed')
  const failedAssessments = assessments.filter((a) => a.status === 'failed' || a.status === 'cancelled')

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评估任务</h1>
          <p className="text-gray-600 mt-1">查看和管理视频质量评估任务</p>
        </div>
        <div className="flex space-x-3">
          {assessments.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={loading}
              className="flex items-center px-4 py-2 text-red-600 hover:text-red-700 border border-red-300 rounded-lg hover:bg-red-50"
            >
              <Trash2 className="h-5 w-5 mr-2" />
              清空全部
            </button>
          )}
          <button
            onClick={loadAssessments}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
            disabled={loading}
          >
            <RefreshCw className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
          <Link
            to="/upload"
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="h-5 w-5 mr-2" />
            新建任务
          </Link>
        </div>
      </div>

      {/* 运行中的任务 */}
      {runningAssessments.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            运行中 ({runningAssessments.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {runningAssessments.map((assessment) => (
              <AssessmentCard
                key={assessment.id}
                assessment={assessment}
                onCancel={() => handleCancel(assessment.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* 等待中的任务 */}
      {pendingAssessments.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            等待中 ({pendingAssessments.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pendingAssessments.map((assessment) => (
              <AssessmentCard
                key={assessment.id}
                assessment={assessment}
                onStart={() => handleStart(assessment.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* 已完成的任务 */}
      {completedAssessments.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            已完成 ({completedAssessments.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedAssessments.map((assessment) => (
              <AssessmentCard key={assessment.id} assessment={assessment} />
            ))}
          </div>
        </div>
      )}

      {/* 失败/取消的任务 */}
      {failedAssessments.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            失败/已取消 ({failedAssessments.length})
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {failedAssessments.map((assessment) => (
              <AssessmentCard key={assessment.id} assessment={assessment} />
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {assessments.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">暂无评估任务</p>
          <Link
            to="/upload"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="h-5 w-5 mr-2" />
            创建新任务
          </Link>
        </div>
      )}
    </div>
  )
}
