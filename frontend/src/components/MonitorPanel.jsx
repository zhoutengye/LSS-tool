import { useState, useEffect } from 'react';
import { Card, Tabs, Statistic, Row, Col, Tag, Alert, Spin } from 'antd';
import { LineChartOutlined, HeatMapOutlined, ThunderboltOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

/**
 * 实时监控面板
 *
 * 显示选中工艺节点的：
 * - 实时数据趋势
 * - Cpk分布直方图
 * - 关键指标统计
 */
export default function MonitorPanel({ selectedNode, isLiveMode = false }) {
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState(null);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    if (selectedNode && isLiveMode) {
      fetchMonitoringData();

      // 实时模式：每5秒刷新一次
      const interval = setInterval(fetchMonitoringData, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedNode, isLiveMode]);

  const fetchMonitoringData = async () => {
    if (!selectedNode) return;

    setLoading(true);
    try {
      // 调用后端监控API
      const res = await axios.get(
        `http://127.0.0.1:8000/api/monitor/node/${selectedNode.data.code}`
      );
      setTrendData(res.data.trend);
      setStatistics(res.data.statistics);
    } catch (err) {
      console.error('获取监控数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 趋势图配置
  const getTrendOption = () => ({
    title: {
      text: `${selectedNode?.data?.name || ''} - 温度趋势`,
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: trendData?.times || [],
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: '温度 (℃)',
      axisLabel: { fontSize: 10 }
    },
    series: [{
      data: trendData?.values || [],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#1890ff' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ]
        }
      },
      markLine: {
        data: [
          ...(statistics?.usl != null ? [{ yAxis: statistics.usl, name: '上限', lineStyle: { color: '#ff4d4f' } }] : []),
          ...(statistics?.target != null ? [{ yAxis: statistics.target, name: '目标', lineStyle: { color: '#52c41a' } }] : []),
          ...(statistics?.lsl != null ? [{ yAxis: statistics.lsl, name: '下限', lineStyle: { color: '#ff4d4f' } }] : [])
        ]
      }
    }],
    grid: { top: 50, right: 20, bottom: 30, left: 50 }
  });

  // Cpk分布图配置
  const getCpkOption = () => ({
    title: {
      text: 'Cpk 能力分布',
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: trendData?.cpk_history?.map((_, i) => `批次${i + 1}`) || [],
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: 'Cpk',
      axisLabel: { fontSize: 10 }
    },
    series: [{
      data: trendData?.cpk_history || [],
      type: 'bar',
      itemStyle: {
        color: (params) => {
          const value = params.value;
          if (value < 0.8) return '#ff4d4f';      // 红色：严重不足
          if (value < 1.33) return '#faad14';    // 黄色：不足
          return '#52c41a';                      // 绿色：良好
        }
      }
    }],
    grid: { top: 50, right: 20, bottom: 30, left: 50 }
  });

  if (!selectedNode) {
    return (
      <Card
        title="📊 工艺监控"
        style={{ height: '100%' }}
      >
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          color: '#999'
        }}>
          <LineChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <div>请点击左侧节点查看详情</div>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={`📊 工艺监控 - ${selectedNode.data?.code} ${selectedNode.data?.name || ''}`}
      extra={
        <Tag color={isLiveMode ? 'green' : 'default'}>
          {isLiveMode ? '🔴 实时' : '⏸️ 历史'}
        </Tag>
      }
      style={{ height: '100%' }}
      bodyStyle={{ padding: '12px' }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin />
        </div>
      ) : (
        <Tabs
          defaultActiveKey="trend"
          items={[
            {
              key: 'trend',
              label: (
                <span>
                  <LineChartOutlined />
                  趋势图
                </span>
              ),
              children: (
                <div>
                  {isLiveMode && (
                    <Alert
                      message="实时监控中"
                      description="数据每5秒自动刷新"
                      type="info"
                      showIcon
                      style={{ marginBottom: 12 }}
                    />
                  )}
                  <ReactECharts option={getTrendOption()} style={{ height: '300px' }} />
                </div>
              )
            },
            {
              key: 'cpk',
              label: (
                <span>
                  <HeatMapOutlined />
                  Cpk分布
                </span>
              ),
              children: (
                <ReactECharts option={getCpkOption()} style={{ height: '300px' }} />
              )
            },
            {
              key: 'stats',
              label: (
                <span>
                  <ThunderboltOutlined />
                  统计指标
                </span>
              ),
              children: (
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Statistic
                      title="当前Cpk"
                      value={statistics?.cpk || 0}
                      precision={2}
                      valueStyle={{
                        color: statistics?.cpk < 1.33 ? '#ff4d4f' : '#52c41a'
                      }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="当前值"
                      value={statistics?.current_value || 0}
                      precision={1}
                      suffix="℃"
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="偏离度"
                      value={statistics?.deviation || 0}
                      precision={2}
                      suffix="σ"
                      valueStyle={{
                        color: Math.abs(statistics?.deviation || 0) > 2 ? '#ff4d4f' : '#52c41a'
                      }}
                    />
                  </Col>
                </Row>
              )
            }
          ]}
        />
      )}
    </Card>
  );
}
