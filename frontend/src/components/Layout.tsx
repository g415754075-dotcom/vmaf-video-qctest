import { Link, useLocation } from 'react-router-dom'
import { Upload, BarChart3, FileText, Home, Settings } from 'lucide-react'
import { cn } from '@/utils'

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { path: '/', label: '首页', icon: Home },
  { path: '/upload', label: '上传', icon: Upload },
  { path: '/assessments', label: '评估任务', icon: BarChart3 },
  { path: '/reports', label: '报告', icon: FileText },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <BarChart3 className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">VMAF QC Test</span>
            </Link>

            {/* 导航链接 */}
            <nav className="flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    )}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>

      {/* 页脚 */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            VMAF Video QC Test - 视频质量评估工具 | 基于 FFmpeg + libvmaf
          </p>
        </div>
      </footer>
    </div>
  )
}
