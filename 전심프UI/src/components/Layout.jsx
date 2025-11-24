import React from 'react';
import { useApp } from '../context/AppContext';
import { MessageSquare, Bookmark, Settings, LogIn, LogOut, User, Sparkles } from 'lucide-react';

const SidebarItem = ({ icon: Icon, label, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-full transition-colors mb-1
      ${isActive 
        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100 font-medium' 
        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
      }`}
  >
    <Icon size={20} />
    <span>{label}</span>
  </button>
);

const Layout = ({ children }) => {
  const { currentView, setCurrentView, isLoggedIn, user, logout } = useApp();

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950 transition-colors duration-300">
      {/* 사이드바 */}
      <aside className="w-64 flex-shrink-0 border-r border-gray-200 dark:border-gray-800 flex flex-col p-4 bg-gray-50 dark:bg-gray-900">
        {/* 로고 */}
        <div 
          className="flex items-center gap-2 px-4 mb-8 cursor-pointer" 
          onClick={() => setCurrentView('chat')}
        >
          <div className="bg-gradient-to-tr from-blue-500 to-purple-500 p-2 rounded-lg">
            <Sparkles className="text-white w-5 h-5" />
          </div>
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
            딸깍리뷰
          </span>
        </div>

        {/* 네비게이션 */}
        <nav className="flex-1">
          <SidebarItem 
            icon={MessageSquare} 
            label="새 분석 시작" 
            isActive={currentView === 'chat'} 
            onClick={() => setCurrentView('chat')} 
          />
          <SidebarItem 
            icon={Bookmark} 
            label="저장된 리뷰" 
            isActive={currentView === 'saved'} 
            onClick={() => setCurrentView('saved')} 
          />
          <SidebarItem 
            icon={Settings} 
            label="설정" 
            isActive={currentView === 'settings'} 
            onClick={() => setCurrentView('settings')} 
          />
        </nav>

        {/* 하단 유저 정보 */}
        <div className="mt-auto pt-4 border-t border-gray-200 dark:border-gray-800">
          {isLoggedIn ? (
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                  {user.name[0]}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium dark:text-white">{user.name}</span>
                  <span className="text-xs text-gray-500">Free Plan</span>
                </div>
              </div>
              <button onClick={logout} className="text-gray-400 hover:text-red-500">
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <SidebarItem 
              icon={LogIn} 
              label="로그인" 
              isActive={currentView === 'login'} 
              onClick={() => setCurrentView('login')} 
            />
          )}
        </div>
      </aside>

      {/* 메인 컨텐츠 영역 */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {children}
      </main>
    </div>
  );
};

export default Layout;