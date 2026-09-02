# 차량 데이터를 Google Sheets 서버에 등록하도록 설정하는 방법

이 앱(`app.py`)은 이제 엑셀/CSV 파일을 업로드하면 그 내용을 **Google Sheets(구글 스프레드시트)**
에 자동으로 등록(저장)하도록 되어 있습니다. 다만 이 기능을 쓰려면 아래 절차대로
"연결 정보(Secrets)"를 한 번 설정해 주어야 합니다. 설정하지 않아도 앱은 정상 작동하지만,
이 경우 업로드한 데이터가 Streamlit 서버 안에만 임시로 저장되어 **앱이 재배포되면 사라집니다.**

설정을 마치면 사이드바에 "✅ Google Sheets 서버에 연결되었습니다"라고 표시됩니다.

---

## 1단계. Google Sheets(구글 스프레드시트) 준비

1. https://sheets.google.com 에서 새 스프레드시트를 만듭니다. (예: "한양고속 차량 데이터")
2. 시트 하단 탭(기본 이름 "시트1")의 이름을 **`차량데이터`** 로 바꿉니다. (app.py 안의
   `WORKSHEET_NAME` 값과 반드시 똑같아야 합니다.)
3. 1행(맨 위 줄)에 아래 7개의 열 제목을 정확히 그대로 입력합니다.

   `차량번호` | `차종` | `담당 노선` | `취득가액` | `최초등록일` | `차령만료일` | `정기검사유효일자`

4. 브라우저 주소창의 스프레드시트 URL을 복사해 둡니다.
   (예: `https://docs.google.com/spreadsheets/d/1AbCdEfG.../edit`)

## 2단계. Google Cloud에서 서비스 계정(로봇 계정) 만들기

앱이 사람 대신 시트에 자동으로 데이터를 쓰려면 "서비스 계정"이라는 전용 로봇 계정이 필요합니다.

1. https://console.cloud.google.com 에 접속해 로그인합니다. (본인 구글 계정이면 됩니다.)
2. 상단에서 새 프로젝트를 하나 만듭니다. (예: "hanyang-bus-app")
3. 좌측 메뉴 **"API 및 서비스" > "라이브러리"** 에서 아래 두 API를 검색해 각각 **사용 설정**합니다.
   - Google Sheets API
   - Google Drive API
4. 좌측 메뉴 **"API 및 서비스" > "사용자 인증 정보"** > 상단 **"+ 사용자 인증 정보 만들기"**
   > **"서비스 계정"** 을 선택합니다.
5. 이름을 적당히 입력하고(예: "bus-app-writer") 만듭니다. 역할(권한) 지정은 건너뛰어도 됩니다.
6. 생성된 서비스 계정을 클릭 > 상단 **"키(Keys)"** 탭 > **"키 추가" > "새 키 만들기"** > **JSON** 선택
   > 다운로드합니다. JSON 파일 하나가 컴퓨터에 저장됩니다. **이 파일은 비밀번호와 같으니
   외부에 유출되지 않도록 주의하세요.**
7. 다운로드한 JSON 파일을 열어보면 `client_email` 값이 있습니다.
   `xxxxx@xxxxx.iam.gserviceaccount.com` 형태의 이메일 주소입니다.

## 3단계. 스프레드시트를 서비스 계정과 공유하기

1. 1단계에서 만든 스프레드시트로 돌아갑니다.
2. 우측 상단 **"공유"** 버튼 클릭 > 2단계 7번에서 확인한 `client_email` 주소를 추가 >
   권한을 **"편집자(Editor)"** 로 설정하고 공유합니다.
   (이 단계를 빼먹으면 "권한 없음(PermissionError)" 오류가 납니다.)

## 4단계. Streamlit Community Cloud에 연결 정보(Secrets) 등록하기

1. https://share.streamlit.io 에서 이 앱(저장소 `Hanyangex/yonduNH`)의 관리 화면으로 들어갑니다.
2. 오른쪽 아래 **"⋮" (점 3개) 메뉴 > "Settings" > "Secrets"** 로 들어갑니다.
3. 아래 형식대로 값을 채워 붙여넣습니다. (`이 폴더의 .streamlit/secrets.toml.example` 파일에도
   같은 템플릿이 있습니다.) `project_id`, `private_key_id`, `private_key`, `client_email`,
   `client_id`, `client_x509_cert_url` 값은 2단계 6번에서 다운로드한 JSON 파일 안의
   같은 이름의 값을 그대로 복사해서 넣으면 됩니다. `spreadsheet` 값에는 1단계 4번에서
   복사한 스프레드시트 URL을 넣습니다.

   ```toml
   [connections.gsheets]
   spreadsheet = "https://docs.google.com/spreadsheets/d/여기에실제URL/edit"
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "...@....iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   ```

4. 저장하면 앱이 자동으로 재시작됩니다. 앱 화면 왼쪽 사이드바 맨 위에
   "✅ Google Sheets 서버에 연결되었습니다"라는 초록색 메시지가 뜨는지 확인하세요.
5. 이제 엑셀/CSV 파일을 업로드하면 구글 스프레드시트의 `차량데이터` 시트에 자동으로
   내용이 등록(덮어쓰기)됩니다. 다른 사람이 같은 앱 주소로 접속해도 같은 데이터를 보게 됩니다.

## (참고) 로컬 컴퓨터에서 먼저 테스트하고 싶다면

`.streamlit/secrets.toml.example` 파일을 복사해서 같은 폴더에 `secrets.toml` 이라는
이름으로 저장하고, 안의 값을 실제 값으로 채운 뒤 아래 명령으로 실행해 테스트할 수 있습니다.

```
pip install -r requirements.txt
streamlit run app.py
```

`secrets.toml` 파일은 `.gitignore`에 이미 등록되어 있어 실수로 GitHub에 올라가지 않습니다.
