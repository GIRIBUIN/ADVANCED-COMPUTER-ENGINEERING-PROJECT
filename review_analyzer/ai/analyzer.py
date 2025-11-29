# RA/review_analyzer/ai/analyzer.py

"""
ChatBot 모듈을 사용하여 리뷰 텍스트에 대한 AI 분석을 수행하는 모듈입니다.
시스템 프롬프트를 정의하고, 분석 요청을 ChatBot에 전달하는 역할을 합니다.
"""

from .chatbot import ChatBot
from flask import current_app
# system_message, ai에 프롬프트에 키워드와 리뷰 데이터 어떻게 넣을지 고민
system_message = """
[지시사항]
당신은 사용자가 입력한 키워드를 중심으로 제품 리뷰를 분석하고 요약하는 전문 분석가입니다.
사용자가 제공한 리뷰 데이터를 기반으로, 입력된 키워드 목록에 대해 다음 정보를 추출하여 반드시 아래 제시된 JSON 형식으로 출력합니다.

1. **제품명 (product_name)**: 리뷰 내용을 기반으로 제품명을 추론하여 기입합니다.
2. **종합 감정 요약 (overall_sentiment_summary)**: 전체 리뷰 내용을 기반으로 한 제품에 대한 종합적인 감정 분석 결과를 한 문장으로 요약합니다.
3. **키워드별 분석 (keywords_analysis)**: 입력된 각 키워드에 대해 다음 세부 정보를 제공합니다.
    a. **키워드 (keyword)**: 분석 대상 키워드 이름.
    b. **긍정 언급 개수 (positive_count)**: 해당 키워드와 관련된 긍정적인 리뷰 문장 또는 언급의 개수를 **정수(Number)**로 계산합니다.
    c. **부정 언급 개수 (negative_count)**: 해당 키워드와 관련된 부정적인 리뷰 문장 또는 언급의 개수를 **정수(Number)**로 계산합니다.
    d. **긍정 요약 (positive_summary)**: 긍정적인 평가 내용을 1~2문장으로 요약합니다.
    e. **부정 요약 (negative_summary)**: 부정적인 평가 내용을 1~2문장으로 요약합니다.

[제약사항]
* 키워드에 대한 직접적인 언급이 부족하거나 관련 내용이 없다면, 해당 요약 섹션에 '해당 키워드에 대한 구체적인 언급이 부족합니다.'라고 명시합니다.
* 반드시 입력받은 키워드 목록에 대해서만 분석을 수행하며, 모든 출력은 JSON 형식이어야 합니다.
* 긍정/부정 개수(count)는 반드시 정수(Number)로 제공해야 하며, 요약 내용 뒤에 추가 정보를 붙이지 않습니다.

[출력 형식]
{
  "product_name": "제품명 (예: 쿠팡 이어폰)",
  "overall_sentiment_summary": "전반적으로 사용자들은 해당 제품에 대해 만족하는 경향이 있으며, 특히 노이즈캔슬링 성능을 높게 평가했습니다.",
  "keywords_analysis": [
    {
      "keyword": "노이즈캔슬링",
      "positive_count": 120,
      "negative_count": 54,
      "positive_summary": "소음을 잘 차단해주는 것이 체감되며 작은 소리를 잘 막아주어 만족도가 높았습니다.",
      "negative_summary": "도서관에서 발생하는 작은 소음도 잘 막아내지 못하며, 고주파 소음에는 취약하다는 의견이 있습니다."
    },
    {
      "keyword": "음질",
      "positive_count": 200,
      "negative_count": 40,
      "positive_summary": "중저음이 괜찮은 수준이고, 통화 음질도 불편함 없이 깨끗하게 들립니다.",
      "negative_summary": "고음에서 소리가 갈라지는 현상이 있으며, 소리가 가벼워서 음악 감상에 별로라는 의견이 있습니다."
    }
  ]
}
"""

_chatbot_instance = None

def get_chatbot():
    """ 챗봇 인스턴스를 가져오거나, 없으면 새로 생성하여 반환합니다. (싱글턴 패턴) """
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = ChatBot(model="gemini-2.0-flash", system_message=system_message)
        _chatbot_instance.init_app(current_app._get_current_object())
    return _chatbot_instance

def analyze_reviews(keywords, review_data):
    chatbot = get_chatbot()
    
    chatbot.reset()
    prompt = f"keywords: {keywords}\nreview data: {review_data}"
    ai_response = chatbot.get_response(user_input=prompt)
    return ai_response
