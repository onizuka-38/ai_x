import pandas as pd

def analyze_dataset_consistency(file_path='data/samples.csv'):
    """
    데이터셋의 라벨링 일관성을 분석하고, 문제가 될 수 있는 부분을 출력합니다.
    """
    try:
        df = pd.read_csv(file_path)
        print("✅ 데이터셋 로드 성공!")
    except FileNotFoundError:
        print(f"❌ 오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        return

    print("\n--- 1. '사실형' vs '추론형' 혼동 분석 ---")
    print("'~이다', '~다'로 끝나는 문장 중 '추론형'으로 라벨링된 의심스러운 사례:\n")
    
    # '~이다', '~다.' 로 끝나는 문장 필터링
    factual_candidates = df[df['user_prompt'].str.endswith('다.') | df['user_prompt'].str.endswith('이다.')]
    
    # 그 중 '추론형'으로 라벨링된 것들
    inconsistent_facts = factual_candidates[factual_candidates['type'] == '추론형']
    
    if not inconsistent_facts.empty:
        for i, row in inconsistent_facts.head(10).iterrows(): # 상위 10개만 출력
            print(f"- [추론형으로 라벨링됨] {row['user_prompt']}")
    else:
        print("해당 조건에서 '추론형'으로 잘못 라벨링된 것으로 의심되는 사례를 찾지 못했습니다.")

    print("\n--- 2. 인용문 유형 분석 ---")
    print("`~고 말했다/밝혔다/전했다` 문장들의 유형 라벨 분포:\n")
    
    quotes = df[df['user_prompt'].str.contains(r'고 (말했다|밝혔다|전했다|강조했다)')]
    
    if not quotes.empty:
        print(quotes['type'].value_counts())
        print("\n☝️ 만약 위 목록에 '사실형' 외 다른 유형이 많다면, 라벨링이 일관되지 않다는 증거입니다.")
    else:
        print("분석할 인용문을 찾지 못했습니다.")

    print("\n--- 3. '~고 한다' 문장들의 확실성 분석 ---")
    print("`~고 한다` 문장들의 확실성 라벨 분포:\n")

    hearsay = df[df['user_prompt'].str.contains(r'고 한다')]

    if not hearsay.empty:
        print(hearsay['truth'].value_counts())
        print("\n☝️ 만약 위 목록에 '확실'과 '불확실'이 섞여 있다면, 라벨링이 일관되지 않다는 증거입니다.")
    else:
        print("분석할 '~고 한다' 문장을 찾지 못했습니다.")


if __name__ == '__main__':
    # samples.csv 파일이 있는 실제 경로를 지정해주세요.
    # 예: 'data/samples.csv' 또는 그냥 'samples.csv'
    analyze_dataset_consistency('data/samples.csv')