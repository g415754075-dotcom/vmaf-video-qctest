import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Trash2, RefreshCw } from 'lucide-react'
import VideoUploader from '@/components/VideoUploader'
import VideoCard from '@/components/VideoCard'
import { useStore } from '@/stores/useStore'
import { getVideos, deleteVideo, updateVideoType, createAssessment } from '@/services/api'
import type { Video } from '@/types'

export default function UploadPage() {
  const navigate = useNavigate()
  const { videos, setVideos, removeVideo, referenceVideoId, setReferenceVideoId } = useStore()
  const [loading, setLoading] = useState(false)
  const [selectedDistortedId, setSelectedDistortedId] = useState<number | null>(null)

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
      if (selectedDistortedId === id) {
        setSelectedDistortedId(null)
      }
    } catch (error) {
      console.error('删除视频失败:', error)
    }
  }

  // 开始评估
  const handleStartAssessment = async () => {
    if (!referenceVideoId || !selectedDistortedId) {
      alert('请选择参考视频和待测视频')
      return
    }

    try {
      const assessment = await createAssessment(referenceVideoId, selectedDistortedId)
      navigate(`/assessments/${assessment.id}`)
    } catch (error) {
      console.error('创建评估任务失败:', error)
      alert('创建评估任务失败')
    }
  }

  // 分离参考视频和待测视频
  const referenceVideo = videos.find((v) => v.id === referenceVideoId)
  const distortedVideos = videos.filter((v) => v.id !== referenceVideoId)

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

            {/* 待测视频 */}
            <div>
              <h3 className="font-medium text-gray-700 mb-3">
                待测视频 <span className="text-red-500">*</span>
              </h3>
              {selectedDistortedId ? (
                <div className="border-2 border-primary-400 rounded-lg p-4 bg-primary-50">
                  <p className="font-medium text-gray-900 truncate">
                    {videos.find((v) => v.id === selectedDistortedId)?.original_filename}
                  </p>
                  <button
                    onClick={() => setSelectedDistortedId(null)}
                    className="mt-2 text-sm text-red-600 hover:text-red-700"
                  >
                    取消选择
                  </button>
                </div>
              ) : (
                <p className="text-gray-500 text-sm">请从下方视频列表中选择一个作为待测视频</p>
              )}
            </div>
          </div>

          {/* 开始评估按钮 */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleStartAssessment}
              disabled={!referenceVideoId || !selectedDistortedId}
              className="flex items-center px-6 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-5 w-5 mr-2" />
              开始评估
            </button>
          </div>
        </div>
      )}

      {/* 视频列表 */}
      {videos.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">已上传的视频 ({videos.length})</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                video={video}
                selected={video.id === selectedDistortedId}
                isReference={video.id === referenceVideoId}
                onSelect={() => {
                  if (video.id !== referenceVideoId) {
                    setSelectedDistortedId(video.id === selectedDistortedId ? null : video.id)
                  }
                }}
                onSetReference={() => handleSetReference(video)}
                onDelete={() => handleDelete(video.id)}
              />
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
