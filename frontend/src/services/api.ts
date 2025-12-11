import axios from 'axios'
import type { Video, Assessment, AssessmentDetail, Report, FrameQuality, ComparisonItem } from '@/types'

const api = axios.create({
  baseURL: '/api',
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

  const response = await api.post<{ video: Video; message: string }>('/upload/complete', formData)
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

export async function createShareLink(id: number, expiresDays: number = 7) {
  const response = await api.post<{ share_url: string; expires_at: string }>(`/reports/${id}/share`, null, {
    params: { expires_days: expiresDays },
  })
  return response.data
}

export function getDownloadUrl(reportId: number, format: 'pdf' | 'excel' | 'json') {
  return `/api/reports/${reportId}/download/${format}`
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
