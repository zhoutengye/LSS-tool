import { useState } from 'react';
import { Layout, Button, Tag, message } from 'antd';
import axios from 'axios';
import ProcessFlow from './components/ProcessFlow';

const { Header, Content, Footer } = Layout;

function App() {
  const [status, setStatus] = useState("未连接");

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

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', color: 'white', fontSize: '1.2rem' }}>
        🧪 稳心颗粒 - 精益六西格玛控制系统
        <div style={{ marginLeft: 'auto' }}>
          <Tag color={status.includes("在线") ? "green" : "red"}>系统状态: {status}</Tag>
          <Button size="small" onClick={checkConnection}>重连</Button>
        </div>
      </Header>
      
      <Content style={{ padding: '20px', background: '#f0f2f5' }}>
        <div style={{ 
          background: 'white', 
          height: '100%', 
          borderRadius: '8px', 
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          overflow: 'hidden' // 防止溢出
        }}>
          {/* 这里加载流程图组件 */}
          <ProcessFlow />
        </div>
      </Content>
      
      <Footer style={{ textAlign: 'center', padding: '10px' }}>
        LSS Engine Demo ©2025 Created by University Team
      </Footer>
    </Layout>
  );
}

export default App;
