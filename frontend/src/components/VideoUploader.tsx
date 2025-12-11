import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { cn, formatFileSize, calculateChunks } from '@/utils'
import { uploadChunk, completeUpload } from '@/services/api'
import { useStore } from '@/stores/useStore'
import type { Video } from '@/types'

interface VideoUploaderProps {
  onUploadComplete?: (video: Video) => void
  videoType?: 'reference' | 'distorted'
}

interface UploadingFile {
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

export default function VideoUploader({ onUploadComplete, videoType = 'distorted' }: VideoUploaderProps) {
  const [uploadingFiles, setUploadingFiles] = useState<Map<string, UploadingFile>>(new Map())
  const { addVideo } = useStore()

  const uploadFile = async (file: File) => {
    const chunkSize = 10 * 1024 * 1024 // 10MB
    const totalChunks = calculateChunks(file.size, chunkSize)

    setUploadingFiles((prev) => {
      const newMap = new Map(prev)
      newMap.set(file.name, { file, progress: 0, status: 'uploading' })
      return newMap
    })

    try {
      // 上传所有分片
      for (let i = 0; i < totalChunks; i++) {
        await uploadChunk(file, i, totalChunks)

        // 更新进度
        const progress = ((i + 1) / totalChunks) * 100
        setUploadingFiles((prev) => {
          const newMap = new Map(prev)
          const item = newMap.get(file.name)
          if (item) {
            newMap.set(file.name, { ...item, progress })
          }
          return newMap
        })
      }

      // 完成上传
      const result = await completeUpload(file.name, totalChunks, file.size, file.name, videoType)

      // 更新状态
      setUploadingFiles((prev) => {
        const newMap = new Map(prev)
        const item = newMap.get(file.name)
        if (item) {
          newMap.set(file.name, { ...item, progress: 100, status: 'completed' })
        }
        return newMap
      })

      // 添加到视频列表
      addVideo(result.video)
      onUploadComplete?.(result.video)

      // 3秒后移除上传项
      setTimeout(() => {
        setUploadingFiles((prev) => {
          const newMap = new Map(prev)
          newMap.delete(file.name)
          return newMap
        })
      }, 3000)
    } catch (error) {
      setUploadingFiles((prev) => {
        const newMap = new Map(prev)
        const item = newMap.get(file.name)
        if (item) {
          newMap.set(file.name, {
            ...item,
            status: 'error',
            error: error instanceof Error ? error.message : '上传失败',
          })
        }
        return newMap
      })
    }
  }

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => {
        uploadFile(file)
      })
    },
    [videoType]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mkv', '.mov', '.avi', '.webm', '.y4m'],
    },
    maxSize: 4 * 1024 * 1024 * 1024, // 4GB
  })

  const removeFile = (filename: string) => {
    setUploadingFiles((prev) => {
      const newMap = new Map(prev)
      newMap.delete(filename)
      return newMap
    })
  }

  return (
    <div className="space-y-4">
      {/* 拖拽上传区域 */}
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-primary-600 font-medium">释放文件开始上传...</p>
        ) : (
          <>
            <p className="text-gray-600 font-medium">拖拽视频文件到这里，或点击选择文件</p>
            <p className="text-sm text-gray-500 mt-2">支持 MP4, MKV, MOV, AVI, WebM, Y4M 格式，最大 4GB</p>
          </>
        )}
      </div>

      {/* 上传列表 */}
      {uploadingFiles.size > 0 && (
        <div className="space-y-2">
          {Array.from(uploadingFiles.entries()).map(([filename, item]) => (
            <div key={filename} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  {item.status === 'uploading' && <Loader2 className="h-5 w-5 text-primary-500 animate-spin" />}
                  {item.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                  {item.status === 'error' && <AlertCircle className="h-5 w-5 text-red-500" />}
                  <div>
                    <p className="font-medium text-gray-900 truncate max-w-xs">{filename}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(item.file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(filename)}
                  className="text-gray-400 hover:text-gray-600"
                  title="移除"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* 进度条 */}
              {item.status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}

              {/* 错误信息 */}
              {item.status === 'error' && item.error && <p className="text-sm text-red-600 mt-1">{item.error}</p>}

              {/* 完成提示 */}
              {item.status === 'completed' && <p className="text-sm text-green-600 mt-1">上传完成</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
