import React from 'react';
import { useApp } from '../context/AppContext';
import { Moon, Sun, Info } from 'lucide-react';

const SettingsPage = () => {
  const { isDarkMode, setIsDarkMode } = useApp();

  return (
    <div className="p-8 max-w-2xl mx-auto animate-fade-in">
      <h2 className="text-2xl font-bold mb-8 dark:text-white">설정</h2>

      <div className="space-y-6">
        {/* 테마 설정 */}
        <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-full ${isDarkMode ? 'bg-gray-800 text-yellow-400' : 'bg-orange-100 text-orange-500'}`}>
              {isDarkMode ? <Moon size={24} /> : <Sun size={24} />}
            </div>
            <div>
              <h3 className="font-medium text-lg dark:text-white">화면 모드</h3>
              <p className="text-gray-500 text-sm">{isDarkMode ? '다크 모드 사용 중' : '라이트 모드 사용 중'}</p>
            </div>
          </div>
          
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)}
            className={`w-14 h-8 rounded-full p-1 transition-colors duration-300 flex items-center ${isDarkMode ? 'bg-blue-600 justify-end' : 'bg-gray-300 justify-start'}`}
          >
            <div className="w-6 h-6 bg-white rounded-full shadow-md" />
          </button>
        </div>

        {/* 앱 정보 */}
        <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 flex items-center gap-4 shadow-sm">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
            <Info size={24} />
          </div>
          <div>
             <h3 className="font-medium text-lg dark:text-white">앱 정보</h3>
             <p className="text-gray-500 text-sm">딸깍리뷰 Version 1.0.0 (Beta)</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;