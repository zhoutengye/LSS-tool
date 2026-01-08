import { Modal, List, Tag, Alert, Space, Typography, Divider } from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

/**
 * 今日操作重点弹窗
 *
 * 工人登录后强制弹出的"晨会"界面：
 * - 显示今日指派给该工人的所有指令
 * - 必须点击"我已阅读并确认"才能进入系统
 * - 展示系统的强制合规能力
 */
export default function BriefingModal({ visible, data, onConfirm }) {
  if (!data) return null;

  // 获取优先级配置
  const getPriorityConfig = (priority) => {
    const configs = {
      'CRITICAL': {
        icon: <ExclamationCircleOutlined />,
        color: 'error',
        text: '紧急'
      },
      'HIGH': {
        icon: <WarningOutlined />,
        color: 'warning',
        text: '重要'
      },
      'MEDIUM': {
        icon: <ClockCircleOutlined />,
        color: 'processing',
        text: '一般'
      },
      'LOW': {
        icon: <ClockCircleOutlined />,
        color: 'default',
        text: '提示'
      }
    };
    return configs[priority] || configs['LOW'];
  };

  // 获取角色标签颜色
  const getRoleColor = (role) => {
    const colors = {
      'Operator': 'blue',
      'QA': 'purple',
      'TeamLeader': 'green',
      'Manager': 'red'
    };
    return colors[role] || 'default';
  };

  // 根据指令数量决定标题样式
  const hasCritical = data.instructions?.some(inst => inst.priority === 'CRITICAL' || inst.priority === 'HIGH');

  return (
    <Modal
      open={visible}
      title={null}
      footer={null}
      closable={false}
      width={700}
      centered
      bodyStyle={{ padding: '24px' }}
    >
      {/* 顶部欢迎信息 */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{ fontSize: '48px', marginBottom: '12px' }}>
          {hasCritical ? '⚠️' : '👋'}
        </div>
        <Title level={3} style={{ marginBottom: '8px' }}>
          早上好，{data.workerName}
        </Title>
        <Text type="secondary">
          {new Date(data.loginTime).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </Text>
      </div>

      {/* 系统状态概览 */}
      <Alert
        message={
          <Space>
            <span>📊</span>
            <span>
              今日您有 <strong>{data.totalInstructions}</strong> 条操作指令，
              其中 <strong>{data.pendingCount}</strong> 条待处理
            </span>
          </Space>
        }
        type={hasCritical ? 'warning' : 'info'}
        showIcon
        style={{ marginBottom: '24px' }}
      />

      {/* 指令列表 */}
      {data.instructions && data.instructions.length > 0 ? (
        <div style={{ marginBottom: '24px' }}>
          <Title level={4} style={{ marginBottom: '16px' }}>
            📋 今日操作重点
          </Title>
          <List
            dataSource={data.instructions}
            renderItem={(item, index) => {
              const priorityConfig = getPriorityConfig(item.priority);

              return (
                <List.Item
                  key={item.id}
                  style={{
                    padding: '16px',
                    background: item.priority === 'CRITICAL' || item.priority === 'HIGH' ? '#fff7e6' : '#fafafa',
                    border: `1px solid ${item.priority === 'CRITICAL' || item.priority === 'HIGH' ? '#ffd591' : '#f0f0f0'}`,
                    borderRadius: '8px',
                    marginBottom: '12px'
                  }}
                >
                  <List.Item.Meta
                    avatar={
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: item.priority === 'CRITICAL' || item.priority === 'HIGH' ? '#ff4d4f' : '#1890ff',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '18px',
                        fontWeight: 'bold'
                      }}>
                        {index + 1}
                      </div>
                    }
                    title={
                      <Space>
                        <Tag color={priorityConfig.color}>
                          {priorityConfig.icon} {priorityConfig.text}
                        </Tag>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {item.node_code && `${item.node_code} · `}
                          {item.batch_id}
                        </span>
                      </Space>
                    }
                    description={
                      <div>
                        <div style={{
                          fontSize: '14px',
                          color: '#262626',
                          marginBottom: '8px',
                          lineHeight: '1.6'
                        }}>
                          {item.content}
                        </div>

                        {/* 证据数据 */}
                        {item.evidence && (
                          <div style={{
                            padding: '8px 12px',
                            background: 'white',
                            border: '1px solid #f0f0f0',
                            borderRadius: '4px',
                            fontSize: '12px',
                            color: '#666'
                          }}>
                            📊 数据证据：
                            {item.evidence.current_value !== undefined && (
                              <span style={{ marginLeft: '8px' }}>
                                当前值: <strong>{item.evidence.current_value}</strong>
                              </span>
                            )}
                            {item.evidence.target_value !== undefined && (
                              <span style={{ marginLeft: '8px' }}>
                                目标值: <strong>{item.evidence.target_value}</strong>
                              </span>
                            )}
                            {item.evidence.cpk !== undefined && (
                              <span style={{ marginLeft: '8px' }}>
                                Cpk: <strong>{item.evidence.cpk}</strong>
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        </div>
      ) : (
        <Alert
          message="✅ 今日无特殊操作指令"
          description="系统运行正常，所有参数在控制范围内。请按标准操作规程执行。"
          type="success"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      <Divider />

      {/* 底部确认按钮 */}
      <div style={{ textAlign: 'center' }}>
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <div style={{
            padding: '12px',
            background: '#e6f7ff',
            border: '1px solid #91d5ff',
            borderRadius: '4px',
            fontSize: '13px'
          }}>
            <strong>⚠️ 重要提示：</strong>
            <div style={{ marginTop: '4px', color: '#666' }}>
              点击确认后，系统将记录您已阅读以上操作指令。请严格按照指令执行，确保生产安全。
            </div>
          </div>

          <button
            onClick={onConfirm}
            style={{
              width: '100%',
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: 'bold',
              color: 'white',
              background: '#52c41a',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => e.target.style.background = '#389e0d'}
            onMouseLeave={(e) => e.target.style.background = '#52c41a'}
          >
            ✅ 我已阅读并确认，进入系统
          </button>
        </Space>
      </div>
    </Modal>
  );
}
