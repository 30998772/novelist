import { useState } from 'react'
import ChatPanel from './components/ChatPanel'
import FileExplorer from './components/FileExplorer'

function App() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="h-screen flex bg-gray-900 text-white">
      {/* 左侧：对话 */}
      <div className="w-1/2 flex flex-col border-r border-gray-700">
        <ChatPanel onRefresh={() => setRefreshKey(k => k + 1)} />
      </div>

      {/* 右侧：文件浏览器 */}
      <div className="w-1/2 flex flex-col">
        <FileExplorer refreshKey={refreshKey} />
      </div>
    </div>
  )
}

export default App
