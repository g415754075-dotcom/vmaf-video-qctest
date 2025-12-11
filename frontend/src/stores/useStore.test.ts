import { describe, it, expect, beforeEach } from 'vitest'
import { useStore } from './useStore'
import type { Video, AssessmentDetail, Report } from '@/types'

describe('useStore', () => {
  beforeEach(() => {
    // 重置 store 状态
    useStore.setState({
      videos: [],
      assessments: [],
      reports: [],
      selectedVideoIds: [],
      referenceVideoId: null,
      uploadingFiles: new Map(),
      loading: false,
    })
  })

  describe('videos', () => {
    const mockVideo: Video = {
      id: 1,
      filename: 'test.mp4',
      original_filename: '测试.mp4',
      file_size: 1024000,
      video_type: 'reference',
      width: 1920,
      height: 1080,
      duration: 120,
      frame_rate: 30,
      frame_count: 3600,
      codec: 'h264',
      bitrate: 5000000,
      created_at: '2024-01-01T00:00:00Z',
    }

    it('应该能够设置视频列表', () => {
      const { setVideos } = useStore.getState()
      setVideos([mockVideo])

      expect(useStore.getState().videos).toHaveLength(1)
      expect(useStore.getState().videos[0]).toEqual(mockVideo)
    })

    it('应该能够添加视频', () => {
      const { addVideo } = useStore.getState()
      addVideo(mockVideo)

      expect(useStore.getState().videos).toHaveLength(1)
    })

    it('应该将新视频添加到列表开头', () => {
      const { setVideos, addVideo } = useStore.getState()
      setVideos([mockVideo])

      const newVideo: Video = { ...mockVideo, id: 2, filename: 'new.mp4' }
      addVideo(newVideo)

      expect(useStore.getState().videos[0].id).toBe(2)
      expect(useStore.getState().videos[1].id).toBe(1)
    })

    it('应该能够移除视频', () => {
      const { setVideos, removeVideo } = useStore.getState()
      setVideos([mockVideo])

      removeVideo(1)
      expect(useStore.getState().videos).toHaveLength(0)
    })

    it('应该只移除指定 ID 的视频', () => {
      const { setVideos, removeVideo } = useStore.getState()
      const video2: Video = { ...mockVideo, id: 2 }
      setVideos([mockVideo, video2])

      removeVideo(1)
      expect(useStore.getState().videos).toHaveLength(1)
      expect(useStore.getState().videos[0].id).toBe(2)
    })
  })

  describe('assessments', () => {
    const mockAssessment: AssessmentDetail = {
      id: 1,
      reference_video_id: 1,
      distorted_video_id: 2,
      status: 'completed',
      progress: 100,
      current_frame: 1800,
      total_frames: 1800,
      vmaf_score: 90,
      vmaf_min: 85,
      vmaf_max: 95,
      ssim_score: 0.98,
      psnr_score: 40,
      vmaf_model: 'vmaf_v0.6.1',
      created_at: '2024-01-01T00:00:00Z',
      reference_video: {} as Video,
      distorted_video: {} as Video,
    }

    it('应该能够设置评估任务列表', () => {
      const { setAssessments } = useStore.getState()
      setAssessments([mockAssessment])

      expect(useStore.getState().assessments).toHaveLength(1)
    })

    it('应该能够更新评估任务', () => {
      const { setAssessments, updateAssessment } = useStore.getState()
      setAssessments([mockAssessment])

      const updated: AssessmentDetail = { ...mockAssessment, progress: 50 }
      updateAssessment(updated)

      expect(useStore.getState().assessments[0].progress).toBe(50)
    })

    it('应该只更新匹配 ID 的评估任务', () => {
      const { setAssessments, updateAssessment } = useStore.getState()
      const assessment2: AssessmentDetail = { ...mockAssessment, id: 2 }
      setAssessments([mockAssessment, assessment2])

      const updated: AssessmentDetail = { ...mockAssessment, progress: 50 }
      updateAssessment(updated)

      expect(useStore.getState().assessments[0].progress).toBe(50)
      expect(useStore.getState().assessments[1].progress).toBe(100)
    })
  })

  describe('reports', () => {
    const mockReport: Report = {
      id: 1,
      name: '测试报告',
      report_type: 'single',
      created_at: '2024-01-01T00:00:00Z',
    }

    it('应该能够设置报告列表', () => {
      const { setReports } = useStore.getState()
      setReports([mockReport])

      expect(useStore.getState().reports).toHaveLength(1)
      expect(useStore.getState().reports[0]).toEqual(mockReport)
    })
  })

  describe('selectedVideoIds', () => {
    it('应该能够切换视频选中状态', () => {
      const { toggleVideoSelection } = useStore.getState()

      toggleVideoSelection(1)
      expect(useStore.getState().selectedVideoIds).toContain(1)

      toggleVideoSelection(1)
      expect(useStore.getState().selectedVideoIds).not.toContain(1)
    })

    it('应该能够选中多个视频', () => {
      const { toggleVideoSelection } = useStore.getState()

      toggleVideoSelection(1)
      toggleVideoSelection(2)
      toggleVideoSelection(3)

      expect(useStore.getState().selectedVideoIds).toHaveLength(3)
      expect(useStore.getState().selectedVideoIds).toEqual([1, 2, 3])
    })

    it('应该能够清空选中', () => {
      const { toggleVideoSelection, clearSelection } = useStore.getState()

      toggleVideoSelection(1)
      toggleVideoSelection(2)
      clearSelection()

      expect(useStore.getState().selectedVideoIds).toHaveLength(0)
    })
  })

  describe('referenceVideoId', () => {
    it('应该能够设置参考视频 ID', () => {
      const { setReferenceVideoId } = useStore.getState()

      setReferenceVideoId(1)
      expect(useStore.getState().referenceVideoId).toBe(1)
    })

    it('应该能够清除参考视频 ID', () => {
      const { setReferenceVideoId } = useStore.getState()

      setReferenceVideoId(1)
      setReferenceVideoId(null)

      expect(useStore.getState().referenceVideoId).toBeNull()
    })
  })

  describe('uploadingFiles', () => {
    it('应该能够设置上传进度', () => {
      const { setUploadProgress } = useStore.getState()

      setUploadProgress('test.mp4', 50, 'uploading')

      const file = useStore.getState().uploadingFiles.get('test.mp4')
      expect(file).toBeDefined()
      expect(file?.progress).toBe(50)
      expect(file?.status).toBe('uploading')
    })

    it('应该能够更新上传进度', () => {
      const { setUploadProgress } = useStore.getState()

      setUploadProgress('test.mp4', 50, 'uploading')
      setUploadProgress('test.mp4', 100, 'completed')

      const file = useStore.getState().uploadingFiles.get('test.mp4')
      expect(file?.progress).toBe(100)
      expect(file?.status).toBe('completed')
    })

    it('应该能够移除上传文件', () => {
      const { setUploadProgress, removeUploadingFile } = useStore.getState()

      setUploadProgress('test.mp4', 100, 'completed')
      removeUploadingFile('test.mp4')

      expect(useStore.getState().uploadingFiles.has('test.mp4')).toBe(false)
    })
  })

  describe('loading', () => {
    it('应该能够设置加载状态', () => {
      const { setLoading } = useStore.getState()

      setLoading(true)
      expect(useStore.getState().loading).toBe(true)

      setLoading(false)
      expect(useStore.getState().loading).toBe(false)
    })
  })
})
