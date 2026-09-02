# 차량 데이터를 Supabase 서버에 등록하도록 설정하는 방법

이 앱(`app.py`)은 이제 엑셀/CSV 파일을 업로드하면 그 내용을 **Supabase(무료 클라우드 데이터베이스)**
에 자동으로 등록(저장)하도록 되어 있습니다. 다만 이 기능을 쓰려면 아래 절차대로
"연결 정보(Secrets)"를 한 번 설정해 주어야 합니다. 설정하지 않아도 앱은 정상 작동하지만,
이 경우 업로드한 데이터가 Streamlit 서버 안에만 임시로 저장되어 **앱이 재배포되면 사라집니다.**

설정을 마치면 사이드바에 "✅ Supabase 서버에 연결되었습니다"라고 표시됩니다.

(참고: 원래는 Google Sheets 연동을 시도했지만, 회사 Google 계정의 조직 정책으로
서비스 계정 키 발급이 막혀 있어 Supabase로 전환했습니다.)

---

## 1단계. Supabase 프로젝트 만들기

1. https://supabase.com 접속 → 우측 상단 **"Start your project"** 클릭 → GitHub 계정 등으로 로그인/가입합니다. (무료 플랜으로 충분합니다.)
2. **"New project"** 클릭 → 프로젝트 이름(예: `hanyang-bus`), 데이터베이스 비밀번호(자동 생성해도 됨), 리전(가까운 곳, 예: Northeast Asia)을 선택하고 생성합니다.
   생성에 1~2분 정도 걸립니다.

## 2단계. 테이블 만들기 (SQL 실행)

1. 왼쪽 메뉴에서 **"SQL Editor"** 클릭 → **"New query"**
2. 아래 SQL을 그대로 붙여넣고 **"Run"** 을 클릭합니다.

   ```sql
   create table vehicle_data (
     id bigint generated always as identity primary key,
     vehicle_no text,
     vehicle_type text,
     route text,
     acquisition_cost numeric,
     first_registered_at date,
     age_expiry_date date,
     inspection_valid_date date,
     created_at timestamptz default now()
   );
   ```

3. 왼쪽 메뉴 **"Table Editor"** 에서 `vehicle_data` 테이블이 생긴 것을 확인합니다.
   (이 테이블은 앱이 자동으로 채우므로 직접 값을 입력할 필요는 없습니다.)

## 3단계. 연결 정보(URL, API 키) 확인하기

1. 왼쪽 메뉴 하단 **"Project Settings"(톱니바퀴 아이콘)** → **"API"** 클릭
2. 아래 두 값을 복사해 둡니다.
   - **Project URL** (예: `https://abcdefghijk.supabase.co`)
   - **service_role secret** 키 (`anon` `public` 키 말고 **service_role** 쪽입니다. "Reveal" 눌러야 보입니다.)

   ⚠️ **service_role 키는 이 데이터베이스의 모든 권한을 가진 매우 민감한 값입니다.**
   Streamlit Cloud의 Secrets 설정(서버 쪽에만 저장되고 브라우저로는 노출되지 않음) 외의
   곳에는 절대 붙여넣거나 공유하지 마세요.

## 4단계. Streamlit Community Cloud에 연결 정보(Secrets) 등록하기

1. https://share.streamlit.io 에서 이 앱(저장소 `Hanyangex/yonduNH`)의 관리 화면으로 들어갑니다.
2. 오른쪽 아래 **"⋮" (점 3개) 메뉴 > "Settings" > "Secrets"** 로 들어갑니다.
3. 아래 형식대로 값을 채워 붙여넣습니다. (이 폴더의 `.streamlit/secrets.toml.example` 파일에도
   같은 템플릿이 있습니다.)

   ```toml
   [supabase]
   url = "https://abcdefghijk.supabase.co"
   key = "여기에 2단계에서 복사한 service_role 키를 붙여넣으세요"
   ```

4. 저장하면 앱이 자동으로 재시작됩니다. 앱 화면 왼쪽 사이드바 맨 위에
   "✅ Supabase 서버에 연결되었습니다"라는 초록색 메시지가 뜨는지 확인하세요.
5. 이제 엑셀/CSV 파일을 업로드하면 Supabase의 `vehicle_data` 테이블에 자동으로
   내용이 등록(전체 교체)됩니다. 다른 사람이 같은 앱 주소로 접속해도 같은 데이터를 보게 됩니다.
   Supabase 대시보드의 "Table Editor" 에서도 데이터를 직접 확인할 수 있습니다.

## (참고) 로컬 컴퓨터에서 먼저 테스트하고 싶다면

`.streamlit/secrets.toml.example` 파일을 복사해서 같은 폴더에 `secrets.toml` 이라는
이름으로 저장하고, 안의 값을 실제 값으로 채운 뒤 아래 명령으로 실행해 테스트할 수 있습니다.

```
pip install -r requirements.txt
streamlit run app.py
```

`secrets.toml` 파일은 `.gitignore`에 이미 등록되어 있어 실수로 GitHub에 올라가지 않습니다.
