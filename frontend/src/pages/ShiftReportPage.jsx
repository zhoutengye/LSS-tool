import { useState } from 'react';
import { Card, Form, Input, InputNumber, Button, Select, Space, message, Modal, Result } from 'antd';
import { SaveOutlined, ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

/**
 * 下工填报单页面
 *
 * 工人下班前填写今日生产数据，系统会自动分析并生成指令。
 *
 * 演示场景：
 * 1. 工人填写异常数据（如温度98℃）
 * 2. 提交后系统自动分析
 * 3. 生成对应的指令给次日工人
 */
export default function ShiftReportPage({ onBack }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [successModal, setSuccessModal] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  // 生成批次号（基于日期）
  const generateBatchId = () => {
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `WX-${dateStr}-${random}`;
  };

  // 提交表单
  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      // 构造提交数据
      const submitData = {
        batch_id: values.batch_id || generateBatchId(),
        worker_id: values.worker_id || 'WORKER_007',
        shift_end_time: new Date().toISOString(),
        data: [
          {
            node_code: 'E04',
            param_code: 'temp',
            value: parseFloat(values.temp),
            unit: '℃'
          },
          {
            node_code: 'E04',
            param_code: 'pressure',
            value: parseFloat(values.pressure),
            unit: 'MPa'
          },
          {
            node_code: 'E04',
            param_code: 'motor_status',
            value: values.motor_status,
            unit: 'status'
          }
        ]
      };

      // 提交到后端
      const res = await axios.post('http://127.0.0.1:8000/api/demo/shift-report', submitData);

      if (res.data.success) {
        setSubmitResult(res.data);
        setSuccessModal(true);
        message.success('填报成功！系统已自动分析数据');
      } else {
        message.error('提交失败：' + (res.data.error || '未知错误'));
      }
    } catch (err) {
      console.error('提交失败:', err);
      message.error('提交失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 填充演示数据（异常场景）
  const fillDemoData = () => {
    form.setFieldsValue({
      batch_id: generateBatchId(),
      worker_id: 'WORKER_007',
      temp: 98.5,        // 故意填一个异常高的温度
      pressure: 2.5,     // 故意填一个异常高的压力
      motor_status: 'abnormal',  // 故意填异常状态
      notes: '设备运行异常，请检查'
    });
    message.info('已填充演示数据（模拟异常场景）');
  };

  // 填充正常数据
  const fillNormalData = () => {
    form.setFieldsValue({
      batch_id: generateBatchId(),
      worker_id: 'WORKER_007',
      temp: 82.0,        // 正常温度
      pressure: 1.5,     // 正常压力
      motor_status: 'normal',
      notes: '生产正常'
    });
    message.info('已填充正常数据');
  };

  return (
    <div style={{
      padding: '24px',
      background: '#f0f2f5',
      minHeight: '100vh'
    }}>
      {/* 顶部导航 */}
      <div style={{ marginBottom: '24px' }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={onBack}
          style={{ marginBottom: '16px' }}
        >
          返回首页
        </Button>
      </div>

      {/* 主表单卡片 */}
      <Card
        title={
          <Space>
            <span>📋</span>
            <span>下工填报单 - 生产日报</span>
          </Space>
        }
        style={{ maxWidth: 800, margin: '0 auto' }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            worker_id: 'WORKER_007',
            temp: 85.0,
            pressure: 1.8,
            motor_status: 'normal'
          }}
        >
          {/* 基本信息 */}
          <Card type="inner" title="基本信息" style={{ marginBottom: '16px' }}>
            <Form.Item
              label="批号"
              name="batch_id"
              rules={[{ required: true, message: '请输入批号' }]}
            >
              <Input placeholder="自动生成或手动输入" />
            </Form.Item>

            <Form.Item
              label="工号"
              name="worker_id"
              rules={[{ required: true, message: '请输入工号' }]}
            >
              <Input placeholder="输入工号，如 WORKER_007" />
            </Form.Item>
          </Card>

          {/* 工艺参数 */}
          <Card type="inner" title="🔧 E04 醇提罐工艺参数" style={{ marginBottom: '16px' }}>
            <Form.Item
              label={
                <Space>
                  <span>🌡️ 提取温度</span>
                  <span style={{ color: '#999', fontSize: '12px' }}>(正常范围: 79-85℃)</span>
                </Space>
              }
              name="temp"
              rules={[{ required: true, message: '请输入温度' }]}
            >
              <InputNumber
                min={0}
                max={120}
                precision={1}
                style={{ width: '100%' }}
                addonAfter="℃"
              />
            </Form.Item>

            <Form.Item
              label={
                <Space>
                  <span>⏱️ 提取压力</span>
                  <span style={{ color: '#999', fontSize: '12px' }}>(正常范围: 1.2-1.8 MPa)</span>
                </Space>
              }
              name="pressure"
              rules={[{ required: true, message: '请输入压力' }]}
            >
              <InputNumber
                min={0}
                max={5}
                precision={1}
                step={0.1}
                style={{ width: '100%' }}
                addonAfter="MPa"
              />
            </Form.Item>
          </Card>

          {/* 设备状态 */}
          <Card type="inner" title="⚙️ 设备状态" style={{ marginBottom: '16px' }}>
            <Form.Item
              label="电机状态"
              name="motor_status"
              rules={[{ required: true, message: '请选择设备状态' }]}
            >
              <Select>
                <Select.Option value="normal">✅ 正常</Select.Option>
                <Select.Option value="abnormal">⚠️ 异常</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="备注"
              name="notes"
            >
              <Input.TextArea
                rows={3}
                placeholder="填写生产过程中的异常情况或其他备注..."
              />
            </Form.Item>
          </Card>

          {/* 快速填充按钮 */}
          <Card type="inner" title="🎬 演示辅助功能" style={{ marginBottom: '24px', background: '#fffbe6' }}>
            <Space>
              <Button onClick={fillNormalData}>
                填充正常数据
              </Button>
              <Button danger onClick={fillDemoData}>
                填充异常数据（触发指令生成）
              </Button>
            </Space>
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              💡 提示：点击"填充异常数据"可以快速模拟异常场景，系统会自动生成对应的指令
            </div>
          </Card>

          {/* 提交按钮 */}
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
              size="large"
              block
            >
              提交日报并下班
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 成功弹窗 */}
      <Modal
        open={successModal}
        onCancel={() => setSuccessModal(false)}
        footer={[
          <Button key="back" onClick={() => setSuccessModal(false)}>
            关闭
          </Button>,
          <Button key="home" type="primary" onClick={onBack}>
            返回首页查看指令
          </Button>
        ]}
      >
        <Result
          icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
          title="填报成功！"
          subTitle="系统已自动分析数据并生成指令"
          extra={
            <div style={{ textAlign: 'left', marginTop: '24px' }}>
              <p><strong>批次号：</strong>{submitResult?.batch_id}</p>
              <p><strong>数据条数：</strong>{submitResult?.data_count}</p>
              <p><strong>生成指令：</strong>{submitResult?.instructions_count} 条</p>
              <p style={{ color: '#52c41a', marginTop: '16px' }}>
                ✅ 您可以下班了，明天上班登录时查看生成的指令
              </p>
            </div>
          }
        />
      </Modal>
    </div>
  );
}
