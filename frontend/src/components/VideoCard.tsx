import { Video as VideoIcon, Clock, Film, Trash2, Star } from 'lucide-react'
import { cn, formatFileSize, formatDuration, formatBitrate } from '@/utils'
import { getStaticUrl } from '@/services/api'
import type { Video } from '@/types'

interface VideoCardProps {
  video: Video
  selected?: boolean
  isReference?: boolean
  onSelect?: () => void
  onSetReference?: () => void
  onDelete?: () => void
}

export default function VideoCard({
  video,
  selected = false,
  isReference = false,
  onSelect,
  onSetReference,
  onDelete,
}: VideoCardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-lg border-2 overflow-hidden transition-all',
        selected ? 'border-primary-500 shadow-md' : 'border-gray-200 hover:border-gray-300',
        isReference && 'ring-2 ring-yellow-400'
      )}
    >
      {/* 缩略图 */}
      <div className="relative aspect-video bg-gray-100">
        {video.thumbnail_path ? (
          <img
            src={getStaticUrl(video.thumbnail_path)}
            alt={video.original_filename}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <VideoIcon className="h-12 w-12 text-gray-400" />
          </div>
        )}

        {/* 参考视频标记 */}
        {isReference && (
          <div className="absolute top-2 left-2 bg-yellow-500 text-white text-xs font-medium px-2 py-1 rounded">
            参考视频
          </div>
        )}

        {/* 时长 */}
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {formatDuration(video.duration)}
          </div>
        )}
      </div>

      {/* 信息 */}
      <div className="p-4">
        <h3 className="font-medium text-gray-900 truncate mb-2" title={video.original_filename}>
          {video.original_filename}
        </h3>

        <div className="space-y-1 text-sm text-gray-500">
          <div className="flex items-center">
            <Film className="h-4 w-4 mr-2" />
            <span>
              {video.width}x{video.height} | {video.codec?.toUpperCase() || 'N/A'}
            </span>
          </div>
          <div className="flex items-center">
            <Clock className="h-4 w-4 mr-2" />
            <span>
              {video.frame_rate?.toFixed(2)} fps | {formatBitrate(video.bitrate || 0)}
            </span>
          </div>
          <div className="text-gray-400">{formatFileSize(video.file_size)}</div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            {onSelect && (
              <button
                onClick={onSelect}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded transition-colors',
                  selected
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                {selected ? '已选择' : '选择'}
              </button>
            )}
            {onSetReference && !isReference && (
              <button
                onClick={onSetReference}
                className="p-1.5 text-gray-400 hover:text-yellow-500 transition-colors"
                title="设为参考视频"
              >
                <Star className="h-5 w-5" />
              </button>
            )}
          </div>
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
              title="删除"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
