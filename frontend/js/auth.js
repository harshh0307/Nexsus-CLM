const Auth = {
  isLoginMode: true,

  init() {
    const loginBtn = document.getElementById('login-btn');
    const toggleLink = document.getElementById('login-toggle-link');
    const nameGroup = document.getElementById('name-group');

    loginBtn.addEventListener('click', () => this.handleAuth());

    toggleLink.addEventListener('click', (e) => {
      e.preventDefault();
      this.isLoginMode = !this.isLoginMode;
      if (this.isLoginMode) {
        loginBtn.textContent = 'Sign In';
        document.getElementById('login-toggle-text').textContent = "Don't have an account?";
        toggleLink.textContent = 'Register';
        nameGroup.style.display = 'none';
      } else {
        loginBtn.textContent = 'Create Account';
        document.getElementById('login-toggle-text').textContent = 'Already have an account?';
        toggleLink.textContent = 'Sign In';
        nameGroup.style.display = 'block';
      }
      document.getElementById('login-error').textContent = '';
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && document.getElementById('login-section').style.display !== 'none') {
        this.handleAuth();
      }
    });

    const token = api.getToken();
    if (token) {
      this.showApp();
    }
  },

  async handleAuth() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const name = document.getElementById('login-name').value.trim();
    const errorEl = document.getElementById('login-error');

    if (!email || !password) {
      errorEl.textContent = 'Email and password are required.';
      return;
    }
    if (!this.isLoginMode && !name) {
      errorEl.textContent = 'Name is required for registration.';
      return;
    }
    if (!email.includes('@')) {
      errorEl.textContent = 'Please enter a valid email address.';
      return;
    }
    if (password.length < 6) {
      errorEl.textContent = 'Password must be at least 6 characters.';
      return;
    }

    errorEl.textContent = '';
    try {
      if (this.isLoginMode) {
        const data = await api.login(email, password);
        api.setToken(data.access_token);
        api.setUser({ email });
        Toast.show('Signed in successfully', 'success');
      } else {
        await api.register(email, password, name);
        Toast.show('Account created! Please sign in.', 'success');
        this.isLoginMode = true;
        document.getElementById('login-btn').textContent = 'Sign In';
        document.getElementById('login-toggle-text').textContent = "Don't have an account?";
        document.getElementById('login-toggle-link').textContent = 'Register';
        document.getElementById('name-group').style.display = 'none';
        document.getElementById('login-password').value = '';
        return;
      }
      this.showApp();
    } catch (err) {
      errorEl.textContent = err.message;
    }
  },

  showApp() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('app-section').style.display = 'flex';
    const user = api.getUser();
    if (user) {
      document.getElementById('user-display').textContent = user.email;
      document.getElementById('user-avatar').textContent = user.email.charAt(0).toUpperCase();
    }
    Screens.init();
    Screens.navigate('dashboard');
  },

  logout() {
    api.setToken(null);
    api.setUser(null);
    document.getElementById('app-section').style.display = 'none';
    document.getElementById('login-section').style.display = 'flex';
    document.getElementById('login-email').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('login-error').textContent = '';
    Toast.show('Signed out', 'info');
  },
};
