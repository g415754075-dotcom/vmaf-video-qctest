import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import VideoCard from './VideoCard'
import type { Video } from '@/types'

describe('VideoCard', () => {
  const mockVideo: Video = {
    id: 1,
    filename: 'test123.mp4',
    original_filename: '测试视频.mp4',
    file_size: 10240000,
    video_type: 'reference',
    width: 1920,
    height: 1080,
    duration: 120.5,
    frame_rate: 30,
    frame_count: 3615,
    codec: 'h264',
    bitrate: 5000000,
    created_at: '2024-01-15T10:30:00Z',
  }

  it('应该渲染视频文件名', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.getByText('测试视频.mp4')).toBeInTheDocument()
  })

  it('应该显示视频分辨率和编码', () => {
    render(<VideoCard video={mockVideo} />)
    // 分辨率和编码在同一行: "1920x1080 | H264"
    expect(screen.getByText(/1920x1080/)).toBeInTheDocument()
    expect(screen.getByText(/H264/)).toBeInTheDocument()
  })

  it('应该显示参考视频标签', () => {
    render(<VideoCard video={mockVideo} isReference={true} />)
    expect(screen.getByText('参考视频')).toBeInTheDocument()
  })

  it('应该在选中状态时显示选中样式', () => {
    const { container } = render(<VideoCard video={mockVideo} selected={true} />)
    // 检查是否有选中的边框
    const card = container.firstChild
    expect(card).toHaveClass('border-primary-500')
  })

  it('应该调用 onSelect 回调', () => {
    const handleSelect = vi.fn()
    render(<VideoCard video={mockVideo} onSelect={handleSelect} />)

    const selectButton = screen.getByText('选择')
    fireEvent.click(selectButton)

    expect(handleSelect).toHaveBeenCalled()
  })

  it('应该显示已选择按钮当 selected 为 true', () => {
    const handleSelect = vi.fn()
    render(<VideoCard video={mockVideo} selected={true} onSelect={handleSelect} />)

    expect(screen.getByText('已选择')).toBeInTheDocument()
  })

  it('应该调用 onDelete 回调', () => {
    const handleDelete = vi.fn()
    render(<VideoCard video={mockVideo} onDelete={handleDelete} />)

    const deleteButton = screen.getByTitle('删除')
    fireEvent.click(deleteButton)

    expect(handleDelete).toHaveBeenCalled()
  })

  it('应该格式化显示视频时长', () => {
    render(<VideoCard video={mockVideo} />)
    // 120.5 秒应该显示为 2:00
    expect(screen.getByText('2:00')).toBeInTheDocument()
  })

  it('应该格式化显示文件大小', () => {
    render(<VideoCard video={mockVideo} />)
    // 10240000 bytes ≈ 9.77 MB
    expect(screen.getByText(/9\.\d+ MB/)).toBeInTheDocument()
  })

  it('应该显示帧率', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.getByText(/30\.00 fps/)).toBeInTheDocument()
  })

  it('应该显示比特率', () => {
    render(<VideoCard video={mockVideo} />)
    expect(screen.getByText(/5\.00 Mbps/)).toBeInTheDocument()
  })

  it('应该显示设为参考视频按钮', () => {
    const handleSetReference = vi.fn()
    render(<VideoCard video={mockVideo} onSetReference={handleSetReference} />)

    const refButton = screen.getByTitle('设为参考视频')
    fireEvent.click(refButton)

    expect(handleSetReference).toHaveBeenCalled()
  })

  it('不应该显示设为参考视频按钮当已是参考视频', () => {
    const handleSetReference = vi.fn()
    render(<VideoCard video={mockVideo} isReference={true} onSetReference={handleSetReference} />)

    expect(screen.queryByTitle('设为参考视频')).not.toBeInTheDocument()
  })
})
