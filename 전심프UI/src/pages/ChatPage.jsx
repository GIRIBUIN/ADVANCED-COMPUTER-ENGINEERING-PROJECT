import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User } from 'lucide-react';
import ResultCard from '../components/ResultCard';

// 하드코딩된 갤럭시 S24 데이터
const MOCK_RESULT = {
  id: Date.now(),
  name: "삼성전자 갤럭시 S24 Ultra 자급제",
  price: "1,698,400원",
  image: "https://image6.coupangcdn.com/image/vendor_inventory/8658/8940866160875fc8745585501867c458316208d145c1df7af79299496660.jpg", // 실제 이미지 예시
  score: "4.3",
  keywords: ["배터리", "발열", "성능"],
  pros: [
    "전작 대비 배터리 효율이 크게 향상되었습니다.",
    "디스플레이 품질이 매우 뛰어나고 밝기도 충분합니다.",
    "S펜 기능이 더욱 정교해졌습니다."
  ],
  cons: [
    "고사양 게임 구동 시 약간의 발열이 느껴집니다.",
    "크기가 커서 한 손 사용이 어렵다는 의견이 있습니다."
  ],
  date: new Date().toLocaleDateString()
};

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatStage, setChatStage] = useState('init'); // init -> url_received -> analyzing -> done
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = () => {
    if (!input.trim()) return;

    // 1. 사용자 메시지 추가
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // 2. 챗봇 응답 로직
    setTimeout(() => {
      let aiMsg;
      
      if (chatStage === 'init') {
        // URL 입력 후 키워드 질문 단계
        aiMsg = { 
          role: 'ai', 
          content: "URL을 확인했습니다. \n어떤 키워드로 분석해드릴까요? (예: 배터리, 카메라, 가성비)" 
        };
        setChatStage('url_received');
      } else if (chatStage === 'url_received') {
        // 키워드 입력 후 결과 출력 단계
        aiMsg = { 
          role: 'ai', 
          content: `${input} 키워드에 대한 분석 결과입니다.`,
          data: { ...MOCK_RESULT, keywords: input.split(',').map(k => k.trim()) } // 입력한 키워드 반영
        };
        setChatStage('done');
      } else {
        // 추가 질문 대응
        aiMsg = { role: 'ai', content: "추가로 궁금한 점이 있으신가요? 새로운 URL을 입력하면 다시 시작합니다." };
      }

      setMessages(prev => [...prev, aiMsg]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 채팅 영역 */}
      <div className="flex-1 overflow-y-auto p-4 pb-32 scrollbar-hide">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-80 animate-fade-in">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-2xl flex items-center justify-center mb-6">
              <Sparkles className="text-blue-600 dark:text-blue-300 w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold mb-2 dark:text-white">안녕하세요!</h2>
            <p className="text-gray-500 dark:text-gray-400">쇼핑몰 URL과 궁금한 키워드를 입력해주세요</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 mb-6 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            {/* 아바타 */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 
              ${msg.role === 'ai' ? 'bg-gradient-to-tr from-blue-500 to-purple-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'}`}>
              {msg.role === 'ai' ? <Sparkles size={16} /> : <User size={16} />}
            </div>
            
            {/* 메시지 내용 */}
            <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-4 py-3 rounded-2xl whitespace-pre-wrap leading-relaxed shadow-sm
                ${msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none'
                }`}>
                {msg.content}
              </div>
              {/* 결과 카드 렌더링 */}
              {msg.data && <ResultCard data={msg.data} />}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4 mb-6 animate-pulse">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white">
               <Sparkles size={16} />
            </div>
            <div className="bg-white dark:bg-gray-800 px-4 py-3 rounded-2xl rounded-bl-none text-gray-500 dark:text-gray-400 text-sm flex items-center gap-2 border border-gray-100 dark:border-gray-700">
               <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
               <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
               <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
               분석 중입니다...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 입력창 영역 (고정) */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white to-transparent dark:from-gray-950 dark:via-gray-950 z-10">
        <div className="max-w-3xl mx-auto relative bg-gray-100 dark:bg-gray-800 rounded-3xl border border-transparent focus-within:border-blue-500 focus-within:bg-white dark:focus-within:bg-gray-900 focus-within:shadow-lg transition-all duration-300">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={chatStage === 'init' ? "여기에 상품 URL을 입력하세요..." : "궁금한 키워드를 입력하세요... (예: 배터리, 소음)"}
            className="w-full bg-transparent border-none focus:ring-0 resize-none py-4 pl-6 pr-14 max-h-32 min-h-[60px] text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            rows={1}
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={`absolute right-2 bottom-2 p-2 rounded-full transition-all
              ${input.trim() && !isLoading
                ? 'bg-blue-600 text-white hover:bg-blue-700' 
                : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'}`}
          >
            <Send size={20} />
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">
          딸깍리뷰는 실수를 할 수 있습니다. 중요한 정보는 다시 확인하세요.
        </p>
      </div>
    </div>
  );
};

export default ChatPage;