// 视频类型
export type VideoType = 'reference' | 'distorted'

// 任务状态
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

// 视频信息
export interface Video {
  id: number
  filename: string
  original_filename: string
  file_size: number
  width?: number
  height?: number
  duration?: number
  frame_rate?: number
  frame_count?: number
  codec?: string
  bitrate?: number
  thumbnail_path?: string
  video_type: VideoType
  created_at: string
}

// 评估任务
export interface Assessment {
  id: number
  reference_video_id: number
  distorted_video_id: number
  status: TaskStatus
  progress: number
  current_frame: number
  total_frames: number
  error_message?: string
  vmaf_score?: number
  vmaf_min?: number
  vmaf_max?: number
  ssim_score?: number
  psnr_score?: number
  ms_ssim_score?: number
  vmaf_model: string
  created_at: string
  started_at?: string
  completed_at?: string
}

// 评估任务详情
export interface AssessmentDetail extends Assessment {
  reference_video: Video
  distorted_video: Video
}

// 逐帧质量数据
export interface FrameQuality {
  frame_num: number
  timestamp: number
  vmaf?: number
  ssim?: number
  psnr?: number
}

// 质量统计
export interface QualityStatistics {
  mean: number
  min: number
  max: number
  median: number
  std: number
  p5: number
  p95: number
}

// 对比项
export interface ComparisonItem {
  assessment_id: number
  video_name: string
  vmaf_score?: number
  ssim_score?: number
  psnr_score?: number
  bitrate?: number
  resolution: string
  codec?: string
}

// 报告
export interface Report {
  id: number
  name: string
  report_type: string
  pdf_path?: string
  excel_path?: string
  json_path?: string
  share_token?: string
  share_expires_at?: string
  created_at: string
}

// 上传进度
export interface UploadProgress {
  filename: string
  uploaded_chunks: number[]
  total_chunks: number
  progress: number
}

// API 响应
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ListResponse<T> {
  items: T[]
  total: number
}
