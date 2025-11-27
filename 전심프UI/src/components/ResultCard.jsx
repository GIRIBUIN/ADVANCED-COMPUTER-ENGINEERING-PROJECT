import React, { useState } from 'react';
import { Star, ThumbsUp, ThumbsDown, Bookmark, Check } from 'lucide-react';
import { useApp } from '../context/AppContext';

const ResultCard = ({ data }) => {
  const { saveReview, isLoggedIn, setCurrentView } = useApp();
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    if (!isLoggedIn) {
      alert("로그인이 필요한 기능입니다.");
      setCurrentView('login');
      return;
    }
    const success = saveReview(data);
    if (success) setIsSaved(true);
  };

  return (
    <div className="w-full max-w-lg bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden mt-2">
      {/* 상품 헤더 */}
      <div className="p-4 flex gap-4 border-b border-gray-100 dark:border-gray-700">
        <div className="w-20 h-20 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
          <img src={data.image} alt={data.name} className="w-full h-full object-cover" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-lg text-gray-900 dark:text-white leading-tight">{data.name}</h3>
          <p className="text-gray-500 text-sm mt-1">{data.price}</p>
          <div className="flex items-center gap-1 mt-2 text-yellow-500">
            <Star fill="currentColor" size={16} />
            <span className="font-bold text-black dark:text-white">{data.score}</span>
            <span className="text-gray-400 text-xs ml-1">/ 5.0</span>
          </div>
        </div>
      </div>

      {/* 분석 내용 */}
      <div className="p-5 space-y-4">
        <div className="flex gap-2 mb-2">
           {data.keywords.map((k, i) => (
             <span key={i} className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300 text-xs rounded-md font-medium">
               #{k}
             </span>
           ))}
        </div>

        <div className="space-y-2">
          <div className="flex items-start gap-3">
            <div className="mt-1 p-1 bg-green-100 dark:bg-green-900/30 rounded text-green-600 dark:text-green-400">
              <ThumbsUp size={14} />
            </div>
            <div className="text-sm text-gray-700 dark:text-gray-300">
              {data.pros.map((txt, i) => <p key={i} className="mb-1">• {txt}</p>)}
            </div>
          </div>
          
          <div className="flex items-start gap-3 pt-2">
             <div className="mt-1 p-1 bg-red-100 dark:bg-red-900/30 rounded text-red-600 dark:text-red-400">
              <ThumbsDown size={14} />
            </div>
            <div className="text-sm text-gray-700 dark:text-gray-300">
              {data.cons.map((txt, i) => <p key={i} className="mb-1">• {txt}</p>)}
            </div>
          </div>
        </div>

        <button 
          onClick={handleSave}
          disabled={isSaved}
          className={`w-full py-2.5 rounded-xl font-medium flex items-center justify-center gap-2 transition-all
            ${isSaved 
              ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 cursor-default' 
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg'
            }`}
        >
          {isSaved ? <><Check size={18} /> 라이브러리에 저장됨</> : <><Bookmark size={18} /> 결과 저장하기</>}
        </button>
      </div>
    </div>
  );
};

export default ResultCard;