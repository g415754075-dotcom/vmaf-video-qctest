import { Link } from 'react-router-dom'
import { Upload, BarChart3, FileText, ArrowRight, Play } from 'lucide-react'

export default function HomePage() {
  const features = [
    {
      icon: Upload,
      title: '视频上传',
      description: '支持拖拽上传、分片上传，最大支持 4GB 视频文件',
      link: '/upload',
    },
    {
      icon: BarChart3,
      title: '质量评估',
      description: '使用 VMAF、SSIM、PSNR 等指标评估视频编解码质量',
      link: '/assessments',
    },
    {
      icon: FileText,
      title: '报告生成',
      description: '自动生成详细的质量评估报告，支持 PDF/Excel 导出',
      link: '/reports',
    },
  ]

  const qualityMetrics = [
    {
      name: 'VMAF',
      description: 'Video Multimethod Assessment Fusion',
      detail: 'Netflix 开发的感知质量评估模型，0-100 分，与人眼感知高度相关',
    },
    {
      name: 'SSIM',
      description: 'Structural Similarity Index',
      detail: '结构相似性指数，衡量图像结构信息的保留程度',
    },
    {
      name: 'PSNR',
      description: 'Peak Signal-to-Noise Ratio',
      detail: '峰值信噪比，传统的图像质量评估指标',
    },
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">VMAF Video QC Test</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          专业的视频质量评估工具，帮助影像效果设计师和视频编解码工程师 快速评估视频编解码后的画质变化
        </p>
        <div className="flex justify-center space-x-4">
          <Link
            to="/upload"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Upload className="h-5 w-5 mr-2" />
            开始上传
          </Link>
          <Link
            to="/assessments"
            className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            <Play className="h-5 w-5 mr-2" />
            查看任务
          </Link>
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">核心功能</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Link
                key={feature.title}
                to={feature.link}
                className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow group"
              >
                <div className="w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-primary-100 transition-colors">
                  <Icon className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 mb-4">{feature.description}</p>
                <span className="inline-flex items-center text-primary-600 text-sm font-medium group-hover:text-primary-700">
                  了解更多
                  <ArrowRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </span>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Quality Metrics */}
      <div className="bg-white rounded-xl border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">支持的质量指标</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {qualityMetrics.map((metric) => (
            <div key={metric.name} className="text-center">
              <div className="text-3xl font-bold text-primary-600 mb-2">{metric.name}</div>
              <div className="text-sm text-gray-500 mb-2">{metric.description}</div>
              <p className="text-gray-600">{metric.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Quality Reference */}
      <div className="bg-gray-50 rounded-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">质量分数参考标准</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-3 px-4 text-left font-medium text-gray-900">指标</th>
                <th className="py-3 px-4 text-center font-medium text-green-600">优秀</th>
                <th className="py-3 px-4 text-center font-medium text-blue-600">良好</th>
                <th className="py-3 px-4 text-center font-medium text-yellow-600">可接受</th>
                <th className="py-3 px-4 text-center font-medium text-red-600">差</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 font-medium">VMAF</td>
                <td className="py-3 px-4 text-center">&gt;90</td>
                <td className="py-3 px-4 text-center">80-90</td>
                <td className="py-3 px-4 text-center">70-80</td>
                <td className="py-3 px-4 text-center">&lt;70</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="py-3 px-4 font-medium">SSIM</td>
                <td className="py-3 px-4 text-center">&gt;0.98</td>
                <td className="py-3 px-4 text-center">0.95-0.98</td>
                <td className="py-3 px-4 text-center">0.90-0.95</td>
                <td className="py-3 px-4 text-center">&lt;0.90</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">PSNR</td>
                <td className="py-3 px-4 text-center">&gt;40dB</td>
                <td className="py-3 px-4 text-center">35-40dB</td>
                <td className="py-3 px-4 text-center">30-35dB</td>
                <td className="py-3 px-4 text-center">&lt;30dB</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
