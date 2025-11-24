import React from 'react';
import { useApp } from '../context/AppContext';
import ResultCard from '../components/ResultCard'; // 카드 재사용
import { BookmarkX } from 'lucide-react';

const SavedPage = () => {
  const { savedItems } = useApp();

  return (
    <div className="p-8 h-full overflow-y-auto">
      <h2 className="text-2xl font-bold mb-6 dark:text-white">내 라이브러리</h2>
      
      {savedItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <BookmarkX size={48} className="mb-4 opacity-50" />
          <p>아직 저장된 분석 결과가 없습니다.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ResultCard는 원래 채팅용이라 마진이 있을 수 있으니 감싸서 렌더링 */}
          {savedItems.map((item, idx) => (
            <div key={idx} className="flex justify-center">
               <ResultCard data={item} /> 
               {/* 필요하다면 ResultCard에 'readOnly' 모드를 추가해서 저장 버튼을 숨길 수도 있습니다 */}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedPage;