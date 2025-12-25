import { create } from 'zustand'
import type { Video, AssessmentDetail, Report } from '@/types'

interface AppState {
  // 视频列表
  videos: Video[]
  setVideos: (videos: Video[]) => void
  addVideo: (video: Video) => void
  removeVideo: (id: number) => void

  // 评估任务列表
  assessments: AssessmentDetail[]
  setAssessments: (assessments: AssessmentDetail[]) => void
  updateAssessment: (assessment: AssessmentDetail) => void

  // 报告列表
  reports: Report[]
  setReports: (reports: Report[]) => void

  // 选中的视频（用于对比）
  selectedVideoIds: number[]
  toggleVideoSelection: (id: number) => void
  clearSelection: () => void

  // 当前参考视频
  referenceVideoId: number | null
  setReferenceVideoId: (id: number | null) => void

  // 选中的待测视频（用于批量评估）
  selectedDistortedIds: number[]
  addDistortedId: (id: number) => void
  removeDistortedId: (id: number) => void
  toggleDistortedId: (id: number) => void
  clearDistortedIds: () => void

  // 上传状态
  uploadingFiles: Map<string, { progress: number; status: string }>
  setUploadProgress: (filename: string, progress: number, status: string) => void
  removeUploadingFile: (filename: string) => void

  // 全局加载状态
  loading: boolean
  setLoading: (loading: boolean) => void
}

export const useStore = create<AppState>((set) => ({
  // 视频
  videos: [],
  setVideos: (videos) => set({ videos }),
  addVideo: (video) => set((state) => ({ videos: [video, ...state.videos] })),
  removeVideo: (id) => set((state) => ({ videos: state.videos.filter((v) => v.id !== id) })),

  // 评估任务
  assessments: [],
  setAssessments: (assessments) => set({ assessments }),
  updateAssessment: (assessment) =>
    set((state) => ({
      assessments: state.assessments.map((a) => (a.id === assessment.id ? assessment : a)),
    })),

  // 报告
  reports: [],
  setReports: (reports) => set({ reports }),

  // 选中的视频
  selectedVideoIds: [],
  toggleVideoSelection: (id) =>
    set((state) => ({
      selectedVideoIds: state.selectedVideoIds.includes(id)
        ? state.selectedVideoIds.filter((vid) => vid !== id)
        : [...state.selectedVideoIds, id],
    })),
  clearSelection: () => set({ selectedVideoIds: [] }),

  // 参考视频
  referenceVideoId: null,
  setReferenceVideoId: (id) => set({ referenceVideoId: id }),

  // 选中的待测视频（用于批量评估）
  selectedDistortedIds: [],
  addDistortedId: (id) =>
    set((state) => ({
      selectedDistortedIds: state.selectedDistortedIds.includes(id)
        ? state.selectedDistortedIds
        : [...state.selectedDistortedIds, id],
    })),
  removeDistortedId: (id) =>
    set((state) => ({
      selectedDistortedIds: state.selectedDistortedIds.filter((vid) => vid !== id),
    })),
  toggleDistortedId: (id) =>
    set((state) => ({
      selectedDistortedIds: state.selectedDistortedIds.includes(id)
        ? state.selectedDistortedIds.filter((vid) => vid !== id)
        : state.selectedDistortedIds.length < 10  // 最多 10 个
          ? [...state.selectedDistortedIds, id]
          : state.selectedDistortedIds,
    })),
  clearDistortedIds: () => set({ selectedDistortedIds: [] }),

  // 上传状态
  uploadingFiles: new Map(),
  setUploadProgress: (filename, progress, status) =>
    set((state) => {
      const newMap = new Map(state.uploadingFiles)
      newMap.set(filename, { progress, status })
      return { uploadingFiles: newMap }
    }),
  removeUploadingFile: (filename) =>
    set((state) => {
      const newMap = new Map(state.uploadingFiles)
      newMap.delete(filename)
      return { uploadingFiles: newMap }
    }),

  // 加载状态
  loading: false,
  setLoading: (loading) => set({ loading }),
}))
