import pandas as pd

file_path = '../crawling/coupang_reviews_final_humanized.xlsx'

# 최대 500개의 행과 50개의 열만 표시하도록 설정
# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 50)

# usecols에는 리스트 형태로 원하는 열 이름을 전달
df = pd.read_excel(file_path, usecols=['review_body'])
clean_df = df.dropna(subset=['review_body'])    # 내용없는 데이터 제거
string_data = clean_df.to_string(
    index=False,
    header=False,
    index_names=False
)   

lines = string_data.strip().split('\n')

# strip()은 문자열 앞뒤 공백 제거
# split('\n')은 각 리뷰를 리스트로 분리

# 모든 리뷰 내용을 공백 하나로 구분하여 하나의 긴 문자열로 합치기
final_string = ' '.join([line.strip() for line in lines])

# 데이터 테스트 출력문
# print(final_string)