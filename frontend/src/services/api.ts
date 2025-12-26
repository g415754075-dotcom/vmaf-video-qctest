import axios from 'axios'
import type { Video, Assessment, AssessmentDetail, Report, FrameQuality, ComparisonItem, BatchAssessment } from '@/types'

// 生产环境使用环境变量配置的 API URL，开发环境使用代理
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
})

// ============ 视频相关 ============

export async function getVideos(params?: { skip?: number; limit?: number; video_type?: string }) {
  const response = await api.get<{ videos: Video[]; total: number }>('/videos', { params })
  return response.data
}

export async function getVideo(id: number) {
  const response = await api.get<Video>(`/videos/${id}`)
  return response.data
}

export async function updateVideoType(id: number, videoType: string) {
  const response = await api.patch<Video>(`/videos/${id}/type`, null, { params: { video_type: videoType } })
  return response.data
}

export async function deleteVideo(id: number) {
  await api.delete(`/videos/${id}`)
}

export async function batchDeleteVideos(videoIds: number[]) {
  const response = await api.post<{ message: string; deleted_count: number; failed_ids: number[] }>(
    '/videos/batch-delete',
    { video_ids: videoIds }
  )
  return response.data
}

export async function clearAllVideos() {
  const response = await api.delete<{ message: string; deleted_count: number; failed_count: number }>(
    '/videos/clear-all'
  )
  return response.data
}

// ============ 上传相关 ============

export async function uploadChunk(
  file: File,
  chunkIndex: number,
  totalChunks: number,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData()
  const chunkSize = 10 * 1024 * 1024 // 10MB
  const start = chunkIndex * chunkSize
  const end = Math.min(start + chunkSize, file.size)
  const chunk = file.slice(start, end)

  formData.append('file', chunk)
  formData.append('filename', file.name)
  formData.append('chunk_index', String(chunkIndex))
  formData.append('total_chunks', String(totalChunks))
  formData.append('file_size', String(file.size))

  const response = await api.post('/upload/chunk', formData, {
    timeout: 300000, // 5分钟超时
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress((e.loaded / e.total) * 100)
      }
    },
  })
  return response.data
}

export async function completeUpload(
  filename: string,
  totalChunks: number,
  fileSize: number,
  originalFilename: string,
  videoType: string = 'distorted'
) {
  const formData = new FormData()
  formData.append('filename', filename)
  formData.append('total_chunks', String(totalChunks))
  formData.append('file_size', String(fileSize))
  formData.append('original_filename', originalFilename)
  formData.append('video_type', videoType)

  // 大文件合并、元信息提取、缩略图生成需要较长时间，设置 5 分钟超时
  const response = await api.post<{ video: Video; message: string }>('/upload/complete', formData, {
    timeout: 300000,
  })
  return response.data
}

export async function getUploadProgress(filename: string, fileSize: number, totalChunks: number) {
  const response = await api.get('/upload/progress', {
    params: { filename, file_size: fileSize, total_chunks: totalChunks },
  })
  return response.data
}

export async function simpleUpload(file: File, videoType: string = 'distorted') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('video_type', videoType)

  const response = await api.post<Video>('/upload/simple', formData)
  return response.data
}

// ============ 评估相关 ============

export async function createAssessment(referenceVideoId: number, distortedVideoId: number) {
  const response = await api.post<Assessment>('/assessments', {
    reference_video_id: referenceVideoId,
    distorted_video_id: distortedVideoId,
  })
  return response.data
}

export async function getAssessments(params?: { skip?: number; limit?: number }) {
  const response = await api.get<{ assessments: AssessmentDetail[]; total: number }>('/assessments', { params })
  return response.data
}

export async function getAssessment(id: number) {
  const response = await api.get<AssessmentDetail>(`/assessments/${id}`)
  return response.data
}

export async function startAssessment(id: number) {
  const response = await api.post(`/assessments/${id}/start`)
  return response.data
}

export async function cancelAssessment(id: number) {
  const response = await api.post(`/assessments/${id}/cancel`)
  return response.data
}

export async function batchDeleteAssessments(assessmentIds: number[]) {
  const response = await api.post<{ message: string; deleted_count: number; failed_ids: number[] }>(
    '/assessments/batch-delete',
    { assessment_ids: assessmentIds }
  )
  return response.data
}

export async function clearAllAssessments() {
  const response = await api.delete<{ message: string; deleted_count: number; skipped_count: number; running_count: number }>(
    '/assessments/clear-all'
  )
  return response.data
}

export async function getFrameData(id: number, params?: { skip?: number; limit?: number }) {
  const response = await api.get<{ assessment_id: number; frames: FrameQuality[]; total_frames: number }>(
    `/assessments/${id}/frames`,
    { params }
  )
  return response.data
}

export async function getStatistics(id: number) {
  const response = await api.get(`/assessments/${id}/statistics`)
  return response.data
}

export async function getProblemFrames(id: number, threshold: number = 70, limit: number = 10) {
  const response = await api.get(`/assessments/${id}/problem-frames`, {
    params: { threshold, limit },
  })
  return response.data
}

export async function compareAssessments(assessmentIds: number[]) {
  const response = await api.post<{ items: ComparisonItem[]; reference_video: Video }>('/assessments/compare', {
    assessment_ids: assessmentIds,
  })
  return response.data
}

// ============ 批量评估相关 ============

export async function createBatchAssessment(referenceVideoId: number, distortedVideoIds: number[]) {
  const response = await api.post<BatchAssessment>('/assessments/batch', {
    reference_video_id: referenceVideoId,
    distorted_video_ids: distortedVideoIds,
  })
  return response.data
}

export async function getBatchStatus(batchId: string) {
  const response = await api.get<BatchAssessment>(`/assessments/batch/${batchId}`)
  return response.data
}

export async function createBatchReport(batchId: string) {
  const response = await api.post<{ report_id: number; name: string; message: string }>(
    `/assessments/batch/${batchId}/report`
  )
  return response.data
}

// ============ 报告相关 ============

export async function createReport(name: string, assessmentIds: number[], includeSections?: string[]) {
  const response = await api.post<Report>('/reports', {
    name,
    assessment_ids: assessmentIds,
    include_sections: includeSections || ['summary', 'charts', 'statistics', 'problem_frames'],
  })
  return response.data
}

export async function getReports(params?: { skip?: number; limit?: number }) {
  const response = await api.get<{ reports: Report[]; total: number }>('/reports', { params })
  return response.data
}

export async function getReport(id: number) {
  const response = await api.get<Report>(`/reports/${id}`)
  return response.data
}

export async function deleteReport(id: number) {
  await api.delete(`/reports/${id}`)
}

export async function batchDeleteReports(reportIds: number[]) {
  const response = await api.post<{ message: string; deleted_count: number; failed_ids: number[] }>(
    '/reports/batch-delete',
    { report_ids: reportIds }
  )
  return response.data
}

export async function clearAllReports() {
  const response = await api.delete<{ message: string; deleted_count: number; failed_count: number }>(
    '/reports/clear-all'
  )
  return response.data
}

export async function createShareLink(id: number, expiresDays: number = 7) {
  const response = await api.post<{ share_url: string; expires_at: string }>(`/reports/${id}/share`, null, {
    params: { expires_days: expiresDays },
  })
  return response.data
}

export function getDownloadUrl(reportId: number, format: 'pdf' | 'excel' | 'json') {
  return `${API_BASE_URL}/api/reports/${reportId}/download/${format}`
}

// 获取图片下载 URL
export function getImageDownloadUrl(
  reportId: number,
  imageType: 'combined' | 'bitrate_vs_size' | 'bitrate_vs_vmaf' | 'vmaf_vs_size'
) {
  return `${API_BASE_URL}/api/reports/${reportId}/download/image/${imageType}`
}

// 获取静态资源 URL（uploads、reports 目录）
export function getStaticUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : '/' + path}`
}

// 获取报告的可用图片列表
export async function getReportImages(reportId: number) {
  const response = await api.get<{
    report_id: number
    report_name: string
    images: Array<{
      type: string
      name: string
      description: string
      download_url: string
    }>
  }>(`/reports/${reportId}/images`)
  return response.data
}

// ============ 配置相关 ============

export async function getConfig() {
  const response = await api.get<{
    max_file_size: number
    allowed_extensions: string[]
    chunk_size: number
    max_concurrent_tasks: number
  }>('/config')
  return response.data
}

export default api
