import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Trash2, RefreshCw, X, CheckSquare, Square } from 'lucide-react'
import VideoUploader from '@/components/VideoUploader'
import VideoCard from '@/components/VideoCard'
import { useStore } from '@/stores/useStore'
import { getVideos, deleteVideo, updateVideoType, createAssessment, createBatchAssessment, clearAllVideos } from '@/services/api'
import type { Video } from '@/types'

export default function UploadPage() {
  const navigate = useNavigate()
  const {
    videos,
    setVideos,
    removeVideo,
    referenceVideoId,
    setReferenceVideoId,
    selectedDistortedIds,
    toggleDistortedId,
    clearDistortedIds,
  } = useStore()
  const [loading, setLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 加载视频列表
  const loadVideos = async () => {
    setLoading(true)
    try {
      const result = await getVideos({ limit: 100 })
      setVideos(result.videos)
    } catch (error) {
      console.error('加载视频列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadVideos()
  }, [])

  // 设置参考视频
  const handleSetReference = async (video: Video) => {
    try {
      await updateVideoType(video.id, 'reference')
      setReferenceVideoId(video.id)
      // 如果这个视频之前被选为待测视频，则移除
      if (selectedDistortedIds.includes(video.id)) {
        toggleDistortedId(video.id)
      }
      loadVideos()
    } catch (error) {
      console.error('设置参考视频失败:', error)
    }
  }

  // 删除视频
  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个视频吗？')) return

    try {
      await deleteVideo(id)
      removeVideo(id)
      if (referenceVideoId === id) {
        setReferenceVideoId(null)
      }
      if (selectedDistortedIds.includes(id)) {
        toggleDistortedId(id)
      }
    } catch (error) {
      console.error('删除视频失败:', error)
    }
  }

  // 清空所有视频
  const handleClearAll = async () => {
    if (!confirm('确定要清空所有视频吗？此操作无法恢复！')) return

    setLoading(true)
    try {
      const result = await clearAllVideos()
      alert(result.message)
      setReferenceVideoId(null)
      clearDistortedIds()
      loadVideos()
    } catch (error) {
      console.error('清空视频失败:', error)
      alert('清空视频失败')
    } finally {
      setLoading(false)
    }
  }

  // 开始评估（单个或批量）
  const handleStartAssessment = async () => {
    if (!referenceVideoId || selectedDistortedIds.length === 0) {
      alert('请选择参考视频和至少一个待测视频')
      return
    }

    setIsSubmitting(true)
    try {
      if (selectedDistortedIds.length === 1) {
        // 单个评估
        const assessment = await createAssessment(referenceVideoId, selectedDistortedIds[0])
        navigate(`/assessments/${assessment.id}`)
      } else {
        // 批量评估
        const batchResult = await createBatchAssessment(referenceVideoId, selectedDistortedIds)
        navigate(`/batch/${batchResult.batch_id}`)
      }
    } catch (error) {
      console.error('创建评估任务失败:', error)
      alert('创建评估任务失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  // 分离参考视频
  const referenceVideo = videos.find((v) => v.id === referenceVideoId)

  // 获取已选择的待测视频列表
  const selectedVideos = videos.filter((v) => selectedDistortedIds.includes(v.id))

  return (
    <div className="space-y-8">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">上传视频</h1>
          <p className="text-gray-600 mt-1">上传参考视频和待测视频，开始质量评估</p>
        </div>
        <button
          onClick={loadVideos}
          className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900"
          disabled={loading}
        >
          <RefreshCw className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
          刷新
        </button>
      </div>

      {/* 上传区域 */}
      <VideoUploader onUploadComplete={() => loadVideos()} />

      {/* 评估设置 */}
      {videos.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">评估设置</h2>

          <div className="grid md:grid-cols-2 gap-6">
            {/* 参考视频 */}
            <div>
              <h3 className="font-medium text-gray-700 mb-3">
                参考视频 <span className="text-red-500">*</span>
              </h3>
              {referenceVideo ? (
                <div className="border-2 border-yellow-400 rounded-lg p-4 bg-yellow-50">
                  <p className="font-medium text-gray-900 truncate">{referenceVideo.original_filename}</p>
                  <p className="text-sm text-gray-500">
                    {referenceVideo.width}x{referenceVideo.height} | {referenceVideo.codec}
                  </p>
                  <button
                    onClick={() => setReferenceVideoId(null)}
                    className="mt-2 text-sm text-red-600 hover:text-red-700"
                  >
                    取消选择
                  </button>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">请从下方视频列表中选择一个作为参考视频</p>
              )}
            </div>

            {/* 待测视频（多选） */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-700">
                  待测视频 <span className="text-red-500">*</span>
                  <span className="ml-2 text-sm text-gray-500">
                    ({selectedDistortedIds.length}/10)
                  </span>
                </h3>
                {selectedDistortedIds.length > 0 && (
                  <button
                    onClick={clearDistortedIds}
                    className="text-sm text-red-600 hover:text-red-700 flex items-center"
                  >
                    <X className="h-4 w-4 mr-1" />
                    清除全部
                  </button>
                )}
              </div>

              {selectedDistortedIds.length > 0 ? (
                <div className="border-2 border-primary-400 rounded-lg p-4 bg-primary-50 max-h-48 overflow-y-auto">
                  <div className="space-y-2">
                    {selectedVideos.map((video) => (
                      <div
                        key={video.id}
                        className="flex items-center justify-between bg-white rounded px-3 py-2"
                      >
                        <span className="text-sm text-gray-900 truncate flex-1">
                          {video.original_filename}
                        </span>
                        <button
                          onClick={() => toggleDistortedId(video.id)}
                          className="ml-2 text-gray-400 hover:text-red-600"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">
                  点击下方视频列表中的复选框选择待测视频（最多 10 个）
                </p>
              )}
            </div>
          </div>

          {/* 开始评估按钮 */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleStartAssessment}
              disabled={!referenceVideoId || selectedDistortedIds.length === 0 || isSubmitting}
              className="flex items-center px-6 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-5 w-5 mr-2" />
              {isSubmitting
                ? '创建中...'
                : selectedDistortedIds.length > 1
                ? `批量评估 (${selectedDistortedIds.length} 个)`
                : '开始评估'}
            </button>
          </div>
        </div>
      )}

      {/* 视频列表 */}
      {videos.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">已上传的视频 ({videos.length})</h2>
            <button
              onClick={handleClearAll}
              disabled={loading}
              className="flex items-center px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Trash2 className="h-4 w-4 mr-1" />
              清空全部
            </button>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video) => (
              <div key={video.id} className="relative">
                {/* 多选复选框（仅对非参考视频显示） */}
                {video.id !== referenceVideoId && (
                  <button
                    onClick={() => toggleDistortedId(video.id)}
                    className="absolute top-2 left-2 z-10 p-1 bg-white rounded shadow-sm hover:bg-gray-100"
                    title={selectedDistortedIds.includes(video.id) ? '取消选择' : '选择此视频'}
                  >
                    {selectedDistortedIds.includes(video.id) ? (
                      <CheckSquare className="h-5 w-5 text-primary-600" />
                    ) : (
                      <Square className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                )}
                <VideoCard
                  video={video}
                  selected={selectedDistortedIds.includes(video.id)}
                  isReference={video.id === referenceVideoId}
                  onSelect={() => {
                    if (video.id !== referenceVideoId) {
                      toggleDistortedId(video.id)
                    }
                  }}
                  onSetReference={() => handleSetReference(video)}
                  onDelete={() => handleDelete(video.id)}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {videos.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          <p>暂无上传的视频，请上传视频开始评估</p>
        </div>
      )}
    </div>
  )
}
