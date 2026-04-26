<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>LiveKlass</title>
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
<div class="container py-5" style="max-width:480px">
  <h1 class="text-center mb-4 fw-bold">LiveKlass</h1>

  <!-- 인증 섹션 -->
  <div id="auth-section">
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button class="nav-link active" id="tab-reg-btn" onclick="showTab('register')">회원가입</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" id="tab-login-btn" onclick="showTab('login')">로그인</button>
      </li>
    </ul>

    <div id="register-tab">
      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-3">회원가입</h5>
          <div class="mb-2">
            <input type="text" id="reg-username" class="form-control"
                   placeholder="아이디 (영문/숫자)">
          </div>
          <div class="mb-3">
            <input type="password" id="reg-password" class="form-control"
                   placeholder="비밀번호 (대소문자+숫자+특수문자, 8-15자)">
          </div>
          <button class="btn btn-primary w-100" onclick="doRegister()">회원가입</button>
          <div id="reg-msg" class="mt-2 small"></div>
        </div>
      </div>
    </div>

    <div id="login-tab" style="display:none">
      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-3">로그인</h5>
          <div class="mb-2">
            <input type="text" id="login-username" class="form-control" placeholder="아이디">
          </div>
          <div class="mb-3">
            <input type="password" id="login-password" class="form-control" placeholder="비밀번호">
          </div>
          <button class="btn btn-success w-100" onclick="doLogin()">로그인</button>
          <div id="login-msg" class="mt-2 small"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 대시보드 섹션 (로그인 후) -->
  <div id="dashboard-section" style="display:none">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title">안녕하세요,
          <span id="username-display" class="text-primary fw-bold"></span>!</h5>
        <p class="text-muted small mb-3">이벤트를 발생시키세요</p>
        <div class="d-grid gap-2">
          <button class="btn btn-outline-primary" onclick="triggerEvent('page_view')">
            페이지 조회
          </button>
          <button class="btn btn-outline-success" onclick="triggerEvent('purchase')">
            구매
          </button>
          <button class="btn btn-outline-danger" onclick="triggerEvent('error')">
            에러 발생
          </button>
          <button class="btn btn-secondary" onclick="doLogout()">로그아웃</button>
        </div>
        <div id="event-msg" class="mt-3 small"></div>
      </div>
    </div>
  </div>
</div>

<script>
  function showTab(tab) {
    document.getElementById('register-tab').style.display = tab === 'register' ? '' : 'none';
    document.getElementById('login-tab').style.display   = tab === 'login'    ? '' : 'none';
    document.getElementById('tab-reg-btn').classList.toggle('active', tab === 'register');
    document.getElementById('tab-login-btn').classList.toggle('active', tab === 'login');
  }

  async function doRegister() {
    const fd = new FormData();
    fd.append('username', document.getElementById('reg-username').value);
    fd.append('password', document.getElementById('reg-password').value);
    const res  = await fetch('/register', {method: 'POST', body: fd});
    const data = await res.json();
    const msg  = document.getElementById('reg-msg');
    if (data.success) {
      msg.className   = 'mt-2 small text-success';
      msg.textContent = '회원가입 완료! 로그인하세요.';
      showTab('login');
    } else {
      msg.className   = 'mt-2 small text-danger';
      msg.textContent = data.message;
    }
  }

  async function doLogin() {
    const fd = new FormData();
    fd.append('username', document.getElementById('login-username').value);
    fd.append('password', document.getElementById('login-password').value);
    const res  = await fetch('/login', {method: 'POST', body: fd});
    const data = await res.json();
    if (data.success) {
      showDashboard(data.username);
    } else {
      const msg = document.getElementById('login-msg');
      msg.className   = 'mt-2 small text-danger';
      msg.textContent = '로그인 실패: ' + data.message;
    }
  }

  async function doLogout() {
    await fetch('/logout', {method: 'POST'});
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('auth-section').style.display      = '';
  }

  async function triggerEvent(eventType) {
    const res  = await fetch('/trigger/' + eventType, {method: 'POST'});
    const data = await res.json();
    const msg  = document.getElementById('event-msg');
    if (data.success) {
      msg.className   = 'small text-success';
      msg.textContent = eventType + ' 이벤트 전송 완료';
    } else {
      msg.className   = 'small text-danger';
      msg.textContent = '이벤트 전송 실패: ' + data.message;
    }
    setTimeout(() => { msg.textContent = ''; }, 3000);
  }

  function showDashboard(username) {
    document.getElementById('auth-section').style.display      = 'none';
    document.getElementById('dashboard-section').style.display = '';
    document.getElementById('username-display').textContent    = username;
  }

  window.onload = async function () {
    const res  = await fetch('/me');
    const data = await res.json();
    if (data.logged_in) showDashboard(data.username);
  };
</script>
</body>
</html>
