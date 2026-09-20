import { useState, useEffect } from 'react'
import { fetchFiles, readFile, FileItem } from '../api'

interface Props {
  refreshKey: number
}

function FileNode({ item, onOpen }: { item: FileItem; onOpen: (path: string) => void }) {
  const [expanded, setExpanded] = useState(false)

  if (item.type === 'directory') {
    return (
      <div>
        <div
          className="flex items-center gap-1 px-2 py-1 hover:bg-gray-700 cursor-pointer text-sm"
          onClick={() => setExpanded(!expanded)}
        >
          <span className="text-yellow-400">{expanded ? '📂' : '📁'}</span>
          <span>{item.name}</span>
        </div>
        {expanded && item.children && (
          <div className="pl-4">
            {item.children.map(child => (
              <FileNode key={child.path} item={child} onOpen={onOpen} />
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      className="flex items-center gap-1 px-2 py-1 hover:bg-gray-700 cursor-pointer text-sm"
      onClick={() => onOpen(item.path)}
    >
      <span className="text-blue-400">📄</span>
      <span className="text-gray-300">{item.name}</span>
      {item.size !== undefined && (
        <span className="text-gray-500 text-xs ml-auto">
          {item.size > 1024 ? `${(item.size / 1024).toFixed(1)}KB` : `${item.size}B`}
        </span>
      )}
    </div>
  )
}

export default function FileExplorer({ refreshKey }: Props) {
  const [items, setItems] = useState<FileItem[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [loading, setLoading] = useState(false)

  const loadFiles = () => {
    fetchFiles().then(setItems)
  }

  useEffect(() => {
    loadFiles()
  }, [refreshKey])

  const handleOpen = async (path: string) => {
    setSelectedFile(path)
    setLoading(true)
    const content = await readFile(path)
    setFileContent(content)
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 顶栏 */}
      <div className="p-3 border-b border-gray-700 flex items-center justify-between">
        <span className="text-sm font-medium">项目文件</span>
        <button
          onClick={loadFiles}
          className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs"
        >
          刷新
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* 文件树 */}
        <div className="w-1/3 border-r border-gray-700 overflow-y-auto">
          {items.map(item => (
            <FileNode key={item.path} item={item} onOpen={handleOpen} />
          ))}
        </div>

        {/* 文件内容 */}
        <div className="flex-1 flex flex-col">
          {selectedFile ? (
            <>
              <div className="p-2 border-b border-gray-700 text-xs text-gray-400">
                {selectedFile}
              </div>
              <div className="flex-1 overflow-auto p-4">
                {loading ? (
                  <div className="text-gray-500 text-sm">加载中...</div>
                ) : (
                  <pre className="text-sm text-gray-200 whitespace-pre-wrap font-mono">
                    {fileContent}
                  </pre>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
              点击文件查看内容
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
