"""
관련도 점수 설정 파일
이 파일에서 뉴스의 관련도 점수 계산 방식을 조정할 수 있습니다.

점수 계산 공식:
  총점 = (MUST_HAVE 키워드 수 × MUST_HAVE_SCORE)
       + (INTEREST 키워드 수 × INTEREST_SCORE)
       + (신뢰 소스 여부 × AUTHORITY_SCORE)

  최대 점수는 MAX_SCORE로 제한됩니다.
"""

# =============================================================================
# 📊 점수 설정 (Score Configuration)
# =============================================================================

# MUST-HAVE 키워드 1개당 점수 (경쟁사, 핵심 기술 등)
MUST_HAVE_SCORE = 30

# INTEREST 키워드 1개당 점수 (관심 주제)
INTEREST_SCORE = 10

# 신뢰 소스(TechCrunch 등)에서 온 뉴스 추가 점수
AUTHORITY_SCORE = 10

# 최대 점수 제한
MAX_SCORE = 100

# =============================================================================
# 🎯 관련성 기준 (Relevance Threshold)
# =============================================================================

# 이 점수 이상이면 "관련 있는 뉴스"로 분류 (Slack 전송)
# 낮추면 더 많은 뉴스, 높이면 더 적은 뉴스
RELEVANCE_THRESHOLD = 20

# =============================================================================
# 🚨 Critical 판정 기준 (Critical Criteria)
# =============================================================================

# MUST-HAVE 키워드가 이 개수 이상이면 Critical
CRITICAL_MUST_HAVE_COUNT = 1

# 다중 소스에서 보도될 때 Critical로 판정하는 소스 수
CRITICAL_MULTI_SOURCE_COUNT = 3

# =============================================================================
# 📈 점수 상한 설정 (Score Caps)
# =============================================================================

# MUST-HAVE 키워드 점수 상한 (예: 2개까지만 인정)
MUST_HAVE_MAX_KEYWORDS = 2
MUST_HAVE_SCORE_CAP = MUST_HAVE_SCORE * MUST_HAVE_MAX_KEYWORDS  # 60

# INTEREST 키워드 점수 상한 (예: 3개까지만 인정)
INTEREST_MAX_KEYWORDS = 3
INTEREST_SCORE_CAP = INTEREST_SCORE * INTEREST_MAX_KEYWORDS  # 30

# =============================================================================
# 🔧 고급 설정 (Advanced Settings)
# =============================================================================

# 긴급 신호(BREAKING 등) + 신뢰 소스 조합 시 Critical 여부
URGENCY_PLUS_AUTHORITY_IS_CRITICAL = True

# 신뢰 소스만으로도 관련 뉴스로 판정할지 여부
AUTHORITY_ALONE_IS_RELEVANT = True


# =============================================================================
# 📋 설정 요약 출력 (디버깅용)
# =============================================================================
def print_scoring_config():
    """현재 점수 설정 출력"""
    print("=== Scoring Configuration ===")
    print(f"MUST_HAVE_SCORE: {MUST_HAVE_SCORE} (cap: {MUST_HAVE_SCORE_CAP})")
    print(f"INTEREST_SCORE: {INTEREST_SCORE} (cap: {INTEREST_SCORE_CAP})")
    print(f"AUTHORITY_SCORE: {AUTHORITY_SCORE}")
    print(f"RELEVANCE_THRESHOLD: {RELEVANCE_THRESHOLD}")
    print(f"MAX_SCORE: {MAX_SCORE}")
    print()
    print("=== Critical Criteria ===")
    print(f"MUST_HAVE count >= {CRITICAL_MUST_HAVE_COUNT}")
    print(f"Multi-source count >= {CRITICAL_MULTI_SOURCE_COUNT}")
    print(f"Urgency + Authority = Critical: {URGENCY_PLUS_AUTHORITY_IS_CRITICAL}")


if __name__ == "__main__":
    print_scoring_config()
