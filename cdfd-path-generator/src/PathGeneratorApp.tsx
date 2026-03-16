import mermaid from 'mermaid';
import { useEffect, useRef, useState } from 'react';

// --- 接口定义 ---
interface TestCase {
  tc_id: string;
  scenario: string;
  path_str: string;
  final_state: string;
}

// --- 专门用于渲染 Mermaid 图像的子组件 ---
const MermaidViewer = ({ code }: { code: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 初始化 Mermaid 配置 (使用暗色主题适配我们的 UI)
    mermaid.initialize({ startOnLoad: false, theme: 'dark' });

    if (code && containerRef.current) {
      // 每次代码更新时，尝试重新渲染
      mermaid.render('mermaid-preview-svg', code)
        .then((result) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = result.svg;
          }
        })
        .catch((error) => {
          console.error("Mermaid 渲染失败:", error);
          if (containerRef.current) {
            containerRef.current.innerHTML = '<div style="color: #ff6b6b; padding: 20px;">图表语法有误，请检查 Mermaid 代码是否闭合或包含非法字符。</div>';
          }
        });
    } else if (!code && containerRef.current) {
      containerRef.current.innerHTML = '<div style="color: #888; padding: 20px;">暂无图表数据</div>';
    }
  }, [code]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'auto',
        background: '#2d2d2d',
        borderRadius: '8px',
        border: '1px solid #444'
      }}
    />
  );
};

// --- 主应用组件 ---
export default function PathGeneratorApp() {
  const [mermaidCode, setMermaidCode] = useState<string>('');
  const [renderCode, setRenderCode] = useState<string>(''); // 专门用于触发图表渲染的代码状态
  const [results, setResults] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);

  // 语法安全版：完美分离声明与连线，防范后端死循环
  // 语法绝对安全版：规避了 Mermaid 解析引擎的形状符号 Bug
  const loadExample = () => {
    const exampleCode = `%% 1. 独立声明所有节点 (全矩形安全声明)
D1["account_file (账户数据库)"]
in_balance["控制输入: balance"]
in_wdraw["控制输入: w_draw"]
in_card["数据输入: card_id"]
in_pass["数据输入: pass"]
P1["Receive_Command"]
P2["Check_Password"]
P3["Withdraw"]
P4["Show_Balance"]
pr_msg_out["输出: pr_msg (错误)"]
e_msg_out["输出: e_msg (异常)"]
cash_out["输出: cash (吐钞)"]
balance_out["输出: balance"]
in_amount["数据输入: amount"]
%% 2. 外部输入连线
in_balance --> P1
in_wdraw --> P1
in_card --> P2
in_pass --> P2

%% 3. 核心业务流转
P1 -- "sel" --> P2
D1 --> P2
in_amount --> P3
%% 4. 分支流转与系统输出
P2 -- "pr_msg" --> pr_msg_out
P2 -- "account1" ---> P3
P2 -- "account2" --> P4
P3 -- "e_msg" --> e_msg_out
P3 -- "cash" --> cash_out
P4 -- "blance"--> balance_out
%% 5. 状态写入 (形成数据闭环)
P3  --> D1`;

    setMermaidCode(exampleCode);
    setRenderCode(`graph LR\n${exampleCode}`);
  };

  const handleGenerate = async () => {
    if (!mermaidCode.trim()) return;
    setLoading(true);

    // 同步更新右侧的可视化图表
    setRenderCode(`graph LR\n${mermaidCode}`);

    try {
      const response = await fetch('http://localhost:8000/api/generate_paths', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mermaid_code: mermaidCode }),
      });
      const resData = await response.json();
      if (resData.status === 'success') {
        setResults(resData.data);
      }
    } catch (error) {
      console.error("生成失败", error);
      alert("无法连接到后端服务，请检查 FastAPI 是否在 8000 端口启动！");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', color: '#fff', background: '#1e1e20', minHeight: '100vh' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>CDFD 架构可视化与路径生成引擎</h2>

      {/* 顶部：左右分栏布局 */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', height: '400px' }}>

        {/* 左侧：代码编辑区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '10px', fontSize: '14px', color: '#aaa' }}>Mermaid 架构定义 (不需写 graph LR)</div>
          <textarea
            value={mermaidCode}
            onChange={(e) => setMermaidCode(e.target.value)}
            placeholder="在此粘贴图表定义代码..."
            style={{
              flex: 1, padding: '15px', fontFamily: 'monospace', fontSize: '14px',
              background: '#2d2d2d', color: '#fff', border: '1px solid #444', borderRadius: '8px',
              resize: 'none'
            }}
          />
        </div>

        {/* 右侧：图形预览区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '10px', fontSize: '14px', color: '#aaa' }}>架构图实时预览</div>
          <MermaidViewer code={renderCode} />
        </div>
      </div>

      {/* 中间：操作按钮 */}
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <button
          onClick={loadExample}
          style={{ marginRight: '15px', padding: '10px 24px', cursor: 'pointer', background: '#555', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '15px' }}
        >
          加载系统架构示例
        </button>
        <button
          onClick={handleGenerate}
          disabled={loading}
          style={{ padding: '10px 24px', cursor: loading ? 'not-allowed' : 'pointer', background: '#4CAF50', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '15px', fontWeight: 'bold' }}
        >
          {loading ? '计算生成中...' : '渲染图表并生成测试路径'}
        </button>
      </div>

      {/* 底部：测试用例表格 */}
      {results.length > 0 && (
        <div style={{ width: '100%', margin: '0 auto', animation: 'fadeIn 0.5s' }}>
          <div style={{ marginBottom: '10px', fontSize: '16px', fontWeight: 'bold', borderLeft: '4px solid #4CAF50', paddingLeft: '10px' }}>
            自动生成的全覆盖测试路径 (共 {results.length} 条)
          </div>
          <table cellPadding={12} style={{ borderCollapse: 'collapse', width: '100%', background: '#2d2d2d', border: '1px solid #444', fontSize: '14px' }}>
            <thead style={{ background: '#3d3d3d' }}>
              <tr>
                <th style={{ border: '1px solid #555', width: '10%' }}>用例编号</th>
                <th style={{ border: '1px solid #555', width: '20%' }}>测试场景</th>
                <th style={{ border: '1px solid #555', width: '55%' }}>完整执行路径 (节点 + 控制条件)</th>
                <th style={{ border: '1px solid #555', width: '15%' }}>系统终态</th>
              </tr>
            </thead>
            <tbody>
              {results.map((tc) => (
                <tr key={tc.tc_id} style={{ borderBottom: '1px solid #444' }}>
                  <td style={{ border: '1px solid #555', textAlign: 'center', fontWeight: 'bold', color: '#4CAF50' }}>{tc.tc_id}</td>
                  <td style={{ border: '1px solid #555' }}>{tc.scenario}</td>
                  <td style={{ border: '1px solid #555', lineHeight: '1.8', fontFamily: 'monospace' }}>{tc.path_str}</td>
                  <td style={{ border: '1px solid #555', textAlign: 'center', background: '#353535' }}>{tc.final_state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}