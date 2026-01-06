import { List, Tag, Button, Badge, Space, Tooltip } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';

/**
 * 待办指令列表组件
 *
 * 这是操作工的核心工作界面：
 * - 显示系统自动生成的工艺指令
 * - 支持执行、标记完成、反馈
 * - 实时更新状态
 */
export default function ActionList({ actions = [], onExecute, onComplete }) {
  // 获取优先级颜色
  const getPriorityColor = (priority) => {
    const colors = {
      'CRITICAL': 'red',
      'HIGH': 'orange',
      'MEDIUM': 'blue',
      'LOW': 'default'
    };
    return colors[priority] || 'default';
  };

  // 获取状态图标和颜色
  const getStatusConfig = (status) => {
    const configs = {
      'Pending': {
        icon: <ClockCircleOutlined />,
        color: 'orange',
        text: '待处理'
      },
      'Read': {
        icon: <ClockCircleOutlined />,
        color: 'blue',
        text: '进行中'
      },
      'Done': {
        icon: <CheckCircleOutlined />,
        color: 'green',
        text: '已完成'
      }
    };
    return configs[status] || configs['Pending'];
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

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 标题栏 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #f0f0f0',
        background: '#fafafa'
      }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 600, fontSize: '14px' }}>
            📋 今日工艺指令
          </span>
          <Badge count={actions.filter(a => a.status === 'Pending').length} showZero>
            <span style={{ color: '#666', fontSize: '12px' }}>
              AI黑带生成
            </span>
          </Badge>
        </Space>
      </div>

      {/* 指令列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
        {actions.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: '#999'
          }}>
            <CheckCircleOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>暂无待处理指令</div>
            <div style={{ fontSize: '12px', marginTop: '8px' }}>
              系统运行正常，所有参数在控制范围内
            </div>
          </div>
        ) : (
          <List
            dataSource={actions}
            renderItem={(item) => {
              const statusConfig = getStatusConfig(item.status);
              return (
                <List.Item
                  key={item.id}
                  style={{
                    padding: '12px',
                    border: '1px solid #f0f0f0',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    background: item.status === 'Pending' ? '#fff7e6' : '#fff',
                    cursor: 'pointer'
                  }}
                  actions={[
                    item.status === 'Pending' && (
                      <Button
                        type="primary"
                        size="small"
                        icon={<CheckCircleOutlined />}
                        onClick={() => onExecute && onExecute(item)}
                      >
                        执行
                      </Button>
                    ),
                    item.status === 'Read' && (
                      <Button
                        size="small"
                        onClick={() => onComplete && onComplete(item)}
                      >
                        完成
                      </Button>
                    )
                  ].filter(Boolean)}
                >
                  <List.Item.Meta
                    avatar={
                      <div style={{ fontSize: '24px' }}>
                        {statusConfig.icon}
                      </div>
                    }
                    title={
                      <Space>
                        <Tag color={getPriorityColor(item.priority)}>
                          {item.priority}
                        </Tag>
                        <Tag color={getRoleColor(item.role)}>
                          {item.role}
                        </Tag>
                        <span style={{ fontSize: '12px', color: '#666' }}>
                          {item.node_code && `${item.node_code} · `}
                          {item.batch_id && `${item.batch_id}`}
                        </span>
                      </Space>
                    }
                    description={
                      <div>
                        <div style={{
                          fontSize: '13px',
                          color: '#262626',
                          marginBottom: '8px',
                          lineHeight: '1.6'
                        }}>
                          {item.content}
                        </div>

                        {/* 证据数据（折叠） */}
                        {item.evidence && (
                          <Tooltip
                            title={
                              <div>
                                <div>Cpk: {item.evidence.cpk?.toFixed(2) || 'N/A'}</div>
                                <div>当前值: {item.evidence.current_value || 'N/A'}</div>
                                {item.evidence.target_value && (
                                  <div>目标值: {item.evidence.target_value}</div>
                                )}
                              </div>
                            }
                          >
                            <Tag style={{ fontSize: '11px', cursor: 'help' }}>
                              📊 查看证据
                            </Tag>
                          </Tooltip>
                        )}

                        {/* 反馈信息 */}
                        {item.feedback && (
                          <div style={{
                            marginTop: '8px',
                            padding: '6px 8px',
                            background: '#f6ffed',
                            border: '1px solid #b7eb8f',
                            borderRadius: '4px',
                            fontSize: '12px',
                            color: '#52c41a'
                          }}>
                            ✓ {item.feedback}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </div>

      {/* 底部统计 */}
      <div style={{
        padding: '8px 16px',
        borderTop: '1px solid #f0f0f0',
        background: '#fafafa',
        fontSize: '11px',
        color: '#666'
      }}>
        <Space split="·">
          <span>待处理: {actions.filter(a => a.status === 'Pending').length}</span>
          <span>进行中: {actions.filter(a => a.status === 'Read').length}</span>
          <span>已完成: {actions.filter(a => a.status === 'Done').length}</span>
        </Space>
      </div>
    </div>
  );
}
