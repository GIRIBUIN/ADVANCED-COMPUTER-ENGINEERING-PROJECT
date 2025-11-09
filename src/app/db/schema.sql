CREATE DATABASE IF NOT EXISTS review_analyzer_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE review_analyzer_db;

-- 1. Users Table
CREATE TABLE USERS(
    user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '사용자 고유 ID. 가입자 수 체크',
    username VARCHAR(255) NOT NULL UNIQUE COMMENT '사용자 닉네임. 중복 불가',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '가입 일'
) COMMENT='사용자 정보 테이블';

-- 2. CATEGORIES Table
CREATE TABLE CATEGORIES(
    category_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '카테고리 고유 ID',
    category_name VARCHAR(255) NOT NULL UNIQUE COMMENT '카테고리 이름. 중복 불가'
) COMMENT='카테고리 정보 테이블';

-- 3. KEYWORDS Table
CREATE TABLE KEYWORDS(
    keyword_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '키워드 고유 ID',
    keyword VARCHAR(255) NOT NULL UNIQUE COMMENT '키워드 텍스트. 중복 불가'
) COMMENT='키워드 정보 테이블';

-- 4. ANALYSES Table
CREATE TABLE ANALYSES(
    analysis_id CHAR(64) PRIMARY KEY COMMENT '분석 고유 ID(url+keyword 해시값)',
    url VARCHAR(2048) NOT NULL COMMENT '분석 대상 URL',
    analysis_text TEXT NOT NULL COMMENT 'AI가 생성한 분석 결과',
    category_id INT NOT NULL COMMENT '카테고리 ID',
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '분석일',
    FOREIGN KEY (category_id) REFERENCES CATEGORIES(category_id)
) COMMENT='리뷰 분석 결과 테이블';

-- 5. LIBRARY Table
CREATE TABLE LIBRARY (
    user_id INT NOT NULL COMMENT '사용자 ID',
    analysis_id CHAR(64) NOT NULL COMMENT '분석 ID',
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '저장일',
    PRIMARY KEY (user_id, analysis_id), -- 동일한 사용자가 동일한 분석을 중복 저장하는 것을 방지
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES ANALYSES(analysis_id) ON DELETE CASCADE
) COMMENT '사용자 라이브러리 테이블';

-- 6. ANALYSIS_KEYWORDS Table
CREATE TABLE ANALYSIS_KEYWORDS (
    analysis_id CHAR(64) NOT NULL COMMENT '분석 ID',
    keyword_id  INT NOT NULL COMMENT '키워드 ID',
    PRIMARY KEY (analysis_id, keyword_id),
    FOREIGN KEY (analysis_id) REFERENCES ANALYSES(analysis_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES KEYWORDS(keyword_id) ON DELETE CASCADE
) COMMENT '분석-키워드 연결 테이블';