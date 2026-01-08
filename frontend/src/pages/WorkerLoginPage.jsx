import { useState } from 'react';
import { Card, Form, Input, Button, message, Space, Typography, Alert } from 'antd';
import { LoginOutlined, IdcardOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import axios from 'axios';
import BriefingModal from '../components/BriefingModal';

const { Title, Text } = Typography;

/**
 * 工人上工登录页面
 *
 * 模拟工人刷卡登录场景：
 * 1. 输入工号（模拟刷卡）
 * 2. 系统查询今日指派给该工人的指令
 * 3. 弹出"今日操作重点"弹窗
 * 4. 工人确认后进入系统
 */
export default function WorkerLoginPage({ onLoginSuccess, onBack }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [briefingData, setBriefingData] = useState(null);

  // 处理登录
  const handleLogin = async (values) => {
    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/demo/login', {
        worker_id: values.worker_id
      });

      if (res.data.success) {
        const briefing = res.data.briefing;

        // 保存简报数据
        setBriefingData({
          workerName: res.data.worker_name,
          loginTime: res.data.login_time,
          totalInstructions: briefing.total_instructions,
          pendingCount: briefing.pending_count,
          instructions: briefing.instructions
        });

        message.success(`欢迎回来，${res.data.worker_name}`);
      } else {
        message.error('登录失败：' + (res.data.error || '未知错误'));
      }
    } catch (err) {
      console.error('登录失败:', err);
      message.error('登录失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 确认简报后进入系统
  const handleBriefingConfirm = () => {
    onLoginSuccess(briefingData);
  };

  return (
    <div style={{
      padding: '24px',
      background: '#f0f2f5',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      {/* 顶部返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={onBack}
        style={{ position: 'absolute', top: '24px', left: '24px' }}
      >
        返回
      </Button>

      {/* 登录卡片 */}
      <Card
        style={{
          width: 450,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>👷‍♂️</div>
          <Title level={3} style={{ marginBottom: '8px' }}>
            工人上工打卡
          </Title>
          <Text type="secondary">
            请刷工卡或输入工号登录
          </Text>
        </div>

        {/* 演示提示 */}
        <Alert
          message="演示提示"
          description="输入任意工号即可登录（如：WORKER_007）。系统会模拟刷卡场景并查询今日指令。"
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />

        {/* 登录表单 */}
        <Form
          form={form}
          onFinish={handleLogin}
          initialValues={{ worker_id: 'WORKER_007' }}
        >
          <Form.Item
            name="worker_id"
            rules={[{ required: true, message: '请输入工号' }]}
          >
            <Input
              prefix={<IdcardOutlined />}
              size="large"
              placeholder="请输入工号"
              autoFocus
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<LoginOutlined />}
              loading={loading}
              size="large"
              block
            >
              上工打卡
            </Button>
          </Form.Item>
        </Form>

        {/* 快速登录按钮 */}
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            快速登录（演示用）：
          </Text>
          <Button
            block
            onClick={() => form.setFieldsValue({ worker_id: 'WORKER_007' })}
          >
            操作工 (WORKER_007)
          </Button>
          <Button
            block
            onClick={() => form.setFieldsValue({ worker_id: 'QA_001' })}
          >
            QA专员 (QA_001)
          </Button>
          <Button
            block
            onClick={() => form.setFieldsValue({ worker_id: 'LEADER_001' })}
          >
            班长 (LEADER_001)
          </Button>
        </Space>

        {/* 系统说明 */}
        <div style={{
          marginTop: '24px',
          padding: '12px',
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#52c41a'
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
            ✅ 系统功能说明：
          </div>
          <div>1. 刷卡登录系统</div>
          <div>2. 查看今日操作重点</div>
          <div>3. 确认后进入工作台</div>
        </div>
      </Card>

      {/* 今日操作重点弹窗 */}
      <BriefingModal
        visible={!!briefingData}
        data={briefingData}
        onConfirm={handleBriefingConfirm}
      />
    </div>
  );
}
