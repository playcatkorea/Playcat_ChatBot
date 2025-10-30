/**
 * Playcat 챗봇 클라이언트
 * 모듈화된 채팅 로직
 */

class PlaycatChat {
  constructor() {
    // API URL (환경에 따라 자동 변경)
    this.API_URL = window.location.hostname === 'localhost'
      ? 'http://localhost:8000'
      : 'https://playcat-chatbot-api.onrender.com';

    this.sessionId = this.generateSessionId();
    this.currentOptions = null;
    this.selectedOption = null;

    this.init();
  }

  /**
   * 초기화
   */
  init() {
    this.cacheElements();
    this.attachEventListeners();
    this.initTheme();
    this.startSession();
  }

  /**
   * DOM 요소 캐싱
   */
  cacheElements() {
    this.elements = {
      messages: document.getElementById('messages'),
      messageInput: document.getElementById('messageInput'),
      sendBtn: document.getElementById('sendBtn'),
      themeToggle: document.getElementById('themeToggle'),
      attachBtn: document.getElementById('attachBtn'),
      loadingOverlay: document.getElementById('loadingOverlay')
    };
  }

  /**
   * 이벤트 리스너 연결
   */
  attachEventListeners() {
    // 전송 버튼
    this.elements.sendBtn.addEventListener('click', () => this.sendMessage());

    // 엔터키
    this.elements.messageInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // 다크모드 토글
    this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());

    // 파일 첨부
    this.elements.attachBtn.addEventListener('click', () => this.handleFileUpload());
  }

  /**
   * 세션 ID 생성
   */
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 채팅 세션 시작
   */
  async startSession() {
    try {
      const response = await fetch(`${this.API_URL}/api/chat/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: this.sessionId })
      });

      const data = await response.json();

      if (data.message) {
        this.addMessage(data.message, 'bot');
      }

      if (data.options && data.options.length > 0) {
        this.showOptions(data.options);
      }

      this.updateStatus('온라인');
    } catch (error) {
      console.error('세션 시작 실패:', error);
      this.showToast('연결 실패. 다시 시도해주세요.', 'error');
      this.updateStatus('오프라인');
    }
  }

  /**
   * 메시지 전송
   */
  async sendMessage() {
    const message = this.elements.messageInput.value.trim();

    if (!message && !this.selectedOption) {
      this.showToast('메시지를 입력해주세요.', 'info');
      return;
    }

    // 사용자 메시지 표시
    if (message) {
      this.addMessage(message, 'user');
    }

    // 입력창 초기화
    this.elements.messageInput.value = '';
    this.elements.messageInput.style.height = 'auto';

    // 타이핑 인디케이터 표시
    this.showTypingIndicator();

    try {
      const response = await fetch(`${this.API_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          message: message,
          selected_option: this.selectedOption
        })
      });

      const data = await response.json();

      // 타이핑 인디케이터 제거
      this.removeTypingIndicator();

      // 응답 메시지 표시
      if (data.response) {
        this.addMessage(data.response, 'bot');
      }

      // 옵션 표시
      if (data.options && data.options.length > 0) {
        this.showOptions(data.options);
      }

      // 선택 초기화
      this.selectedOption = null;

    } catch (error) {
      console.error('메시지 전송 실패:', error);
      this.removeTypingIndicator();
      this.showToast('메시지 전송에 실패했습니다.', 'error');
    }
  }

  /**
   * 메시지 추가
   */
  addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'bot' ? '🐱' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = this.getCurrentTime();

    content.appendChild(bubble);
    content.appendChild(time);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    this.elements.messages.appendChild(messageDiv);
    this.scrollToBottom();
  }

  /**
   * 옵션 버튼 표시
   */
  showOptions(options) {
    this.currentOptions = options;

    const optionsDiv = document.createElement('div');
    optionsDiv.className = 'message bot';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🐱';

    const content = document.createElement('div');
    content.className = 'message-content';

    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'options';

    options.forEach(option => {
      const btn = document.createElement('button');
      btn.className = 'option-btn';
      btn.textContent = option.label || option.text;
      btn.onclick = () => this.selectOption(option.id);
      optionsContainer.appendChild(btn);
    });

    content.appendChild(optionsContainer);
    optionsDiv.appendChild(avatar);
    optionsDiv.appendChild(content);

    this.elements.messages.appendChild(optionsDiv);
    this.scrollToBottom();
  }

  /**
   * 옵션 선택
   */
  selectOption(optionId) {
    this.selectedOption = optionId;

    // 선택된 옵션 텍스트 찾기
    const option = this.currentOptions.find(opt => opt.id === optionId);
    if (option) {
      this.addMessage(option.label || option.text, 'user');
    }

    // 모든 옵션 버튼 비활성화
    const optionButtons = document.querySelectorAll('.option-btn');
    optionButtons.forEach(btn => {
      btn.disabled = true;
      btn.style.opacity = '0.5';
    });

    // 메시지 전송
    this.sendMessage();
  }

  /**
   * 타이핑 인디케이터 표시
   */
  showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot typing-message';
    indicator.id = 'typingIndicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🐱';

    const content = document.createElement('div');
    content.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';

    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('span');
      dot.className = 'typing-dot';
      bubble.appendChild(dot);
    }

    content.appendChild(bubble);
    indicator.appendChild(avatar);
    indicator.appendChild(content);

    this.elements.messages.appendChild(indicator);
    this.scrollToBottom();
  }

  /**
   * 타이핑 인디케이터 제거
   */
  removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
      indicator.remove();
    }
  }

  /**
   * 파일 업로드 처리
   */
  async handleFileUpload() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      this.showLoading();

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', this.sessionId);

      try {
        const response = await fetch(`${this.API_URL}/api/image/upload`, {
          method: 'POST',
          body: formData
        });

        const data = await response.json();

        this.hideLoading();

        if (data.filename) {
          this.showToast('이미지가 업로드되었습니다.', 'success');
          this.addMessage('이미지를 업로드했습니다. 분석 중입니다...', 'user');

          // AI 분석 요청
          this.sendMessage();
        } else {
          this.showToast('업로드 실패. 다시 시도해주세요.', 'error');
        }
      } catch (error) {
        console.error('업로드 실패:', error);
        this.hideLoading();
        this.showToast('업로드에 실패했습니다.', 'error');
      }
    };
    input.click();
  }

  /**
   * 스크롤 하단으로
   */
  scrollToBottom() {
    this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
  }

  /**
   * 현재 시간 반환
   */
  getCurrentTime() {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  }

  /**
   * 다크모드 토글
   */
  toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    this.elements.themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
  }

  /**
   * 테마 초기화
   */
  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    this.elements.themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
  }

  /**
   * 상태 업데이트
   */
  updateStatus(status) {
    const statusText = document.querySelector('.chat-status span:last-child');
    if (statusText) {
      statusText.textContent = status;
    }
  }

  /**
   * 로딩 표시
   */
  showLoading() {
    this.elements.loadingOverlay.classList.add('active');
  }

  /**
   * 로딩 숨김
   */
  hideLoading() {
    this.elements.loadingOverlay.classList.remove('active');
  }

  /**
   * 토스트 알림
   */
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `<span style="font-size: 20px;">${icon}</span><span>${message}</span>`;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('active'), 100);

    setTimeout(() => {
      toast.classList.remove('active');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
  window.playcatChat = new PlaycatChat();
});
