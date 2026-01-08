import { useState, useEffect } from 'react';
import { Layout, Button, Tag, message, Switch, Space, Typography, Divider, Menu, Popconfirm } from 'antd';
import { ThunderboltOutlined, HistoryOutlined, ReloadOutlined, BarChartOutlined, HomeOutlined, ExperimentOutlined, LoginOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import axios from 'axios';
import ProcessFlow from './components/ProcessFlow';
import ActionList from './components/ActionList';
import MonitorPanel from './components/MonitorPanel';
import LSSToolsPage from './pages/LSSToolsPage';
import IntelligentAnalysisPage from './pages/IntelligentAnalysisPage';
import ShiftReportPage from './pages/ShiftReportPage';
import WorkerLoginPage from './pages/WorkerLoginPage';

const { Header, Content, Sider, Footer } = Layout;
const { Text } = Typography;

function App() {
  // 页面切换
  const [currentPage, setCurrentPage] = useState('home'); // 'home', 'lss-tools', 'intelligent-analysis', 'shift-report', 'worker-login'
  const [workerInfo, setWorkerInfo] = useState(null); // 登录后的工人信息

  // 系统状态
  const [status, setStatus] = useState("未连接");

  // 模式切换：实时 vs 仿真
  const [isLiveMode, setIsLiveMode] = useState(false);

  // 选中的节点（用于右侧监控面板）
  const [selectedNode, setSelectedNode] = useState(null);

  // 指令列表
  const [actions, setActions] = useState([]);
  const [loadingActions, setLoadingActions] = useState(false);

  // 测试连接
  const checkConnection = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/test');
      setStatus(`在线 (${res.data.temperature}℃)`);
      message.success("后端连接正常");
    } catch (err) {
      setStatus("离线");
      message.error("后端未启动");
    }
  };

  // 加载指令列表
  const fetchInstructions = async () => {
    setLoadingActions(true);
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/instructions', {
        params: {
          role: 'Operator',  // 默认显示操作工的指令
          status: 'Pending,Read'
        }
      });
      setActions(res.data.instructions || []);
    } catch (err) {
      console.error('获取指令失败:', err);
    } finally {
      setLoadingActions(false);
    }
  };

  // 初始化和定时刷新
  useEffect(() => {
    checkConnection();
    fetchInstructions();

    // 每30秒刷新一次指令列表
    const interval = setInterval(fetchInstructions, 30000);
    return () => clearInterval(interval);
  }, []);

  // 切换模式
  const handleModeChange = (checked) => {
    setIsLiveMode(checked);
    message.info(checked ? '已切换到实时监控模式' : '已切换到仿真模式');
  };

  // 执行指令
  const handleExecuteAction = async (action) => {
    try {
      await axios.post(`http://127.0.0.1:8000/api/instructions/${action.id}/read`);
      message.success('指令已标记为进行中');
      fetchInstructions(); // 刷新列表
    } catch (err) {
      message.error('操作失败');
    }
  };

  // 完成指令
  const handleCompleteAction = async (action) => {
    try {
      // 这里可以添加反馈输入框
      await axios.post(`http://127.0.0.1:8000/api/instructions/${action.id}/done`, {
        feedback: '已完成'
      });
      message.success('指令已完成');
      fetchInstructions(); // 刷新列表
    } catch (err) {
      message.error('操作失败');
    }
  };

  // 重置演示环境
  const handleResetDemo = async () => {
    try {
      await axios.delete('http://127.0.0.1:8000/api/demo/reset');
      message.success('演示环境已重置');
      fetchInstructions(); // 刷新指令列表
    } catch (err) {
      message.error('重置失败');
    }
  };

  // 工人登录成功
  const handleLoginSuccess = (info) => {
    setWorkerInfo(info);
    setCurrentPage('home');
    message.success('登录成功，已确认今日操作重点');
    fetchInstructions(); // 刷新指令列表
  };

  return (
    <Layout style={{ height: '100vh' }}>
      {/* 顶部导航栏 */}
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        color: 'white',
        fontSize: '1.2rem',
        background: '#001529',
        padding: '0 24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.5rem' }}>🧪</span>
          <span>稳心颗粒 - 智能工艺指挥台</span>
        </div>

        <div style={{ marginLeft: '40px', display: 'flex', gap: '8px' }}>
          <Button
            type={currentPage === 'home' ? 'primary' : 'text'}
            icon={<HomeOutlined />}
            onClick={() => setCurrentPage('home')}
            style={{ color: currentPage === 'home' ? 'white' : 'rgba(255,255,255,0.65)' }}
          >
            工艺监控
          </Button>
          <Button
            type={currentPage === 'lss-tools' ? 'primary' : 'text'}
            icon={<BarChartOutlined />}
            onClick={() => setCurrentPage('lss-tools')}
            style={{ color: currentPage === 'lss-tools' ? 'white' : 'rgba(255,255,255,0.65)' }}
          >
            LSS工具箱
          </Button>
          <Button
            type={currentPage === 'intelligent-analysis' ? 'primary' : 'text'}
            icon={<ExperimentOutlined />}
            onClick={() => setCurrentPage('intelligent-analysis')}
            style={{ color: currentPage === 'intelligent-analysis' ? 'white' : 'rgba(255,255,255,0.65)' }}
          >
            AI黑带专家
          </Button>
          <Divider type="vertical" style={{ height: 24, borderColor: 'rgba(255,255,255,0.3)' }} />
          {/* Demo 功能按钮 */}
          <Button
            type={currentPage === 'shift-report' ? 'primary' : 'text'}
            icon={<EditOutlined />}
            onClick={() => setCurrentPage('shift-report')}
            style={{ color: currentPage === 'shift-report' ? 'white' : 'rgba(255,255,255,0.65)' }}
          >
            下工填报
          </Button>
          <Button
            type={currentPage === 'worker-login' ? 'primary' : 'text'}
            icon={<LoginOutlined />}
            onClick={() => setCurrentPage('worker-login')}
            style={{ color: currentPage === 'worker-login' ? 'white' : 'rgba(255,255,255,0.65)' }}
          >
            上工登录
          </Button>
        </div>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Demo 重置按钮 */}
          <Popconfirm
            title="重置演示环境"
            description="这将清空所有生产数据和指令，知识图谱保留。确定要重置吗？"
            onConfirm={handleResetDemo}
            okText="确定重置"
            cancelText="取消"
          >
            <Button size="small" icon={<DeleteOutlined />} danger>
              重置演示
            </Button>
          </Popconfirm>

          {/* 模式切换 */}
          <Space>
            <Text style={{ color: 'white', fontSize: '14px' }}>
              {isLiveMode ? <ThunderboltOutlined /> : <HistoryOutlined />}
              {isLiveMode ? '实时监控' : '仿真模式'}
            </Text>
            <Switch
              checked={isLiveMode}
              onChange={handleModeChange}
              checkedChildren="实时"
              unCheckedChildren="仿真"
            />
          </Space>

          <Divider type="vertical" style={{ height: 24, borderColor: 'rgba(255,255,255,0.3)' }} />

          {/* 系统状态 */}
          <Tag color={status.includes("在线") ? "green" : "red"}>
            {status}
          </Tag>
          <Button size="small" icon={<ReloadOutlined />} onClick={checkConnection}>
            重连
          </Button>
        </div>
      </Header>

      {/* 主体内容 */}
      {currentPage === 'intelligent-analysis' ? (
        <IntelligentAnalysisPage />
      ) : currentPage === 'lss-tools' ? (
        <LSSToolsPage />
      ) : currentPage === 'shift-report' ? (
        <ShiftReportPage onBack={() => setCurrentPage('home')} />
      ) : currentPage === 'worker-login' ? (
        <WorkerLoginPage
          onLoginSuccess={handleLoginSuccess}
          onBack={() => setCurrentPage('home')}
        />
      ) : (
        <Layout>
        {/* 左侧：工艺流程图 */}
        <Content style={{
          padding: '16px',
          background: '#f0f2f5',
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'white',
            height: '100%',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            overflow: 'hidden',
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              top: '12px',
              left: '12px',
              zIndex: 1000,
              background: 'rgba(255,255,255,0.9)',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#666',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              💡 点击区块展开/折叠，双击节点查看详情，右键节点查看风险
            </div>

            {/* 传递模式给流程图组件 */}
            <ProcessFlow
              isLiveMode={isLiveMode}
              onNodeSelect={setSelectedNode}
            />
          </div>
        </Content>

        {/* 右侧：监控面板 + 指令列表 */}
        <Sider
          width={400}
          style={{
            background: 'white',
            borderLeft: '1px solid #f0f0f0'
          }}
        >
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* 上半部分：监控面板（50%高度） */}
            <div style={{ height: '50%', borderBottom: '1px solid #f0f0f0' }}>
              <MonitorPanel
                selectedNode={selectedNode}
                isLiveMode={isLiveMode}
              />
            </div>

            {/* 下半部分：指令列表（50%高度） */}
            <div style={{ height: '50%', overflow: 'hidden' }}>
              <ActionList
                actions={actions}
                onExecute={handleExecuteAction}
                onComplete={handleCompleteAction}
              />
            </div>
          </div>
        </Sider>
      </Layout>
      )}
      {/* 底部 */}
      <Footer style={{
        textAlign: 'center',
        padding: '10px',
        background: '#fafafa',
        borderTop: '1px solid #f0f0f0'
      }}>
        <Space split="·">
          <span>LSS Engine v2.0 - 智能指挥系统</span>
          <span>©2025 Created by University Team</span>
          <Tag color="blue">AI黑带大脑</Tag>
        </Space>
      </Footer>
    </Layout>
  );
}

export default App;

