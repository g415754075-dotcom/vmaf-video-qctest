import { useEffect, useState } from 'react'
import { RefreshCw, Share2, Trash2, FileText, Table, Code, Image, ChevronDown } from 'lucide-react'
import { getReports, deleteReport, createShareLink, getDownloadUrl, getImageDownloadUrl, clearAllReports } from '@/services/api'
import { formatDate, cn } from '@/utils'
import type { Report } from '@/types'

// 图片下载下拉菜单组件
function ImageDownloadMenu({ reportId }: { reportId: number }) {
  const [isOpen, setIsOpen] = useState(false)

  const imageOptions = [
    { type: 'combined' as const, label: '合并图（三图并排）' },
    { type: 'bitrate_vs_size' as const, label: '码率 vs 文件大小' },
    { type: 'bitrate_vs_vmaf' as const, label: '码率 vs VMAF' },
    { type: 'vmaf_vs_size' as const, label: 'VMAF vs 文件大小' },
  ]

  const handleDownloadImage = (imageType: 'combined' | 'bitrate_vs_size' | 'bitrate_vs_vmaf' | 'vmaf_vs_size') => {
    window.open(getImageDownloadUrl(reportId, imageType), '_blank')
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 text-purple-600 hover:bg-purple-50 rounded flex items-center"
        title="下载图片"
      >
        <Image className="h-5 w-5" />
        <ChevronDown className="h-3 w-3 ml-0.5" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[180px]">
            {imageOptions.map((opt) => (
              <button
                key={opt.type}
                onClick={() => handleDownloadImage(opt.type)}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(false)

  const loadReports = async () => {
    setLoading(true)
    try {
      const result = await getReports({ limit: 100 })
      setReports(result.reports)
    } catch (error) {
      console.error('加载报告列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个报告吗？')) return

    try {
      await deleteReport(id)
      setReports(reports.filter((r) => r.id !== id))
    } catch (error) {
      console.error('删除报告失败:', error)
      alert('删除报告失败')
    }
  }

  const handleShare = async (id: number) => {
    try {
      const result = await createShareLink(id, 7)
      const shareUrl = window.location.origin + result.share_url
      await navigator.clipboard.writeText(shareUrl)
      alert(`分享链接已复制到剪贴板！\n有效期至: ${formatDate(result.expires_at)}`)
    } catch (error) {
      console.error('生成分享链接失败:', error)
      alert('生成分享链接失败')
    }
  }

  const handleDownload = (reportId: number, format: 'pdf' | 'excel' | 'json') => {
    window.open(getDownloadUrl(reportId, format), '_blank')
  }

  const handleClearAll = async () => {
    if (!confirm('确定要清空所有报告吗？此操作无法恢复！')) return

    setLoading(true)
    try {
      const result = await clearAllReports()
      alert(result.message)
      loadReports()
    } catch (error) {
      console.error('清空报告失败:', error)
      alert('清空报告失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">评估报告</h1>
          <p className="text-gray-600 mt-1">查看和下载质量评估报告</p>
        </div>
        <div className="flex space-x-3">
          {reports.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={loading}
              className="flex items-center px-4 py-2 text-red-600 hover:text-red-700 border border-red-300 rounded-lg hover:bg-red-50"
            >
              <Trash2 className="h-5 w-5 mr-2" />
              清空全部
            </button>
          )}
          <button
            onClick={loadReports}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
            disabled={loading}
          >
            <RefreshCw className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>
      </div>

      {/* 报告列表 */}
      {reports.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-500">报告名称</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-500">类型</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-500">创建时间</th>
                <th className="py-3 px-4 text-left text-sm font-medium text-gray-500">下载</th>
                <th className="py-3 px-4 text-right text-sm font-medium text-gray-500">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <p className="font-medium text-gray-900">{report.name}</p>
                  </td>
                  <td className="py-4 px-4">
                    <span
                      className={cn(
                        'inline-flex px-2 py-1 text-xs font-medium rounded',
                        report.report_type === 'single'
                          ? 'bg-blue-100 text-blue-700'
                          : report.report_type === 'batch'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-purple-100 text-purple-700'
                      )}
                    >
                      {report.report_type === 'single' ? '单视频' : report.report_type === 'batch' ? '批量对比' : '对比'}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-sm text-gray-500">{formatDate(report.created_at)}</td>
                  <td className="py-4 px-4">
                    <div className="flex space-x-2">
                      {report.pdf_path && (
                        <button
                          onClick={() => handleDownload(report.id, 'pdf')}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                          title="下载 PDF"
                        >
                          <FileText className="h-5 w-5" />
                        </button>
                      )}
                      {report.excel_path && (
                        <button
                          onClick={() => handleDownload(report.id, 'excel')}
                          className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                          title="下载 Excel"
                        >
                          <Table className="h-5 w-5" />
                        </button>
                      )}
                      {report.json_path && (
                        <button
                          onClick={() => handleDownload(report.id, 'json')}
                          className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
                          title="下载 JSON"
                        >
                          <Code className="h-5 w-5" />
                        </button>
                      )}
                      {/* 图片下载按钮（仅批量报告显示） */}
                      {(report.report_type === 'batch' || report.report_type === 'comparison') && (
                        <ImageDownloadMenu reportId={report.id} />
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => handleShare(report.id)}
                        className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded"
                        title="分享"
                      >
                        <Share2 className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(report.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="删除"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">暂无报告</p>
          <p className="text-sm text-gray-400 mt-1">完成评估任务后可生成报告</p>
        </div>
      )}
    </div>
  )
}
