import React, { useState } from 'react';
import PathGeneratorApp from './PathGeneratorApp'; // 引入我们写好的核心引擎

// --- 1. 独立封装的登录页面组件 ---
const LoginScreen = ({ onLogin }: { onLogin: () => void }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // 模拟前端写死的鉴权逻辑 (后续可替换为请求后端的真实的鉴权 API)
    if (username === 'admin' && password === '123456') {
      onLogin(); // 登录成功，触发状态切换
    } else {
      setError('账号或密码错误 (测试提示: admin / 123456)');
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#1e1e20', fontFamily: 'sans-serif' }}>
      <form
        onSubmit={handleLogin}
        style={{ background: '#2d2d2d', padding: '40px 50px', borderRadius: '12px', boxShadow: '0 8px 24px rgba(0,0,0,0.6)', width: '320px', color: '#fff', border: '1px solid #444' }}
      >
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50', marginBottom: '10px' }}>✦ MBT 测试引擎</div>
          <div style={{ fontSize: '14px', color: '#aaa' }}>系统身份验证</div>
        </div>

        {error && (
          <div style={{ color: '#ff6b6b', background: 'rgba(255, 107, 107, 0.1)', padding: '10px', borderRadius: '4px', marginBottom: '20px', fontSize: '13px', textAlign: 'center', border: '1px solid #ff6b6b' }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#ccc' }}>工程师账号</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{ width: '100%', padding: '12px', boxSizing: 'border-box', background: '#1e1e20', border: '1px solid #555', color: '#fff', borderRadius: '6px', outline: 'none', transition: 'border 0.2s' }}
            placeholder="输入 admin"
            required
          />
        </div>

        <div style={{ marginBottom: '35px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#ccc' }}>访问密码</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{ width: '100%', padding: '12px', boxSizing: 'border-box', background: '#1e1e20', border: '1px solid #555', color: '#fff', borderRadius: '6px', outline: 'none', transition: 'border 0.2s' }}
            placeholder="输入 123456"
            required
          />
        </div>

        <button
          type="submit"
          style={{ width: '100%', padding: '14px', background: '#4CAF50', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold', transition: 'background 0.2s', letterSpacing: '2px' }}
          onMouseOver={(e) => e.currentTarget.style.background = '#43a047'}
          onMouseOut={(e) => e.currentTarget.style.background = '#4CAF50'}
        >
          进 入 系 统
        </button>
      </form>
    </div>
  );
};

// --- 2. 顶部导航栏 (包含退出功能) ---
const NavBar = ({ onLogout }: { onLogout: () => void }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 30px', height: '60px', background: '#252526', color: '#fff', borderBottom: '1px solid #333', fontFamily: 'sans-serif' }}>
    <div style={{ fontSize: '18px', fontWeight: 'bold', letterSpacing: '1px' }}>
      <span style={{ color: '#4CAF50', marginRight: '8px' }}>⎈</span>
      模型驱动自动化测试平台
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* 模拟一个用户头像圆圈 */}
        <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#4CAF50', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '14px', fontWeight: 'bold' }}>A</div>
        <span style={{ fontSize: '14px', color: '#ccc' }}>Admin_QA</span>
      </div>
      <button
        onClick={onLogout}
        style={{ padding: '6px 16px', background: 'transparent', color: '#ff6b6b', border: '1px solid #ff6b6b', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', transition: 'all 0.2s' }}
        onMouseOver={(e) => { e.currentTarget.style.background = '#ff6b6b'; e.currentTarget.style.color = '#fff'; }}
        onMouseOut={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#ff6b6b'; }}
      >
        退出登录
      </button>
    </div>
  </div>
);

// --- 3. 应用程序主入口 (状态路由控制) ---
function App() {
  // 核心状态：控制用户是否已登录
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 未登录状态：渲染登录屏幕
  if (!isLoggedIn) {
    return <LoginScreen onLogin={() => setIsLoggedIn(true)} />;
  }

  // 已登录状态：渲染导航栏 + 核心业务应用
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#1e1e20' }}>
      <NavBar onLogout={() => setIsLoggedIn(false)} />

      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* 将我们之前写好的核心引擎挂载在这里 */}
        <PathGeneratorApp />
      </div>
    </div>
  );
}

export default App;